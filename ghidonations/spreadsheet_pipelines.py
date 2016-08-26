import cStringIO
import csv
import gc
import logging

import cloudstorage as gcs
import ghidonations.tools.keys
import pipeline
from ghidonations.tools import util, spreadsheet
from google.appengine.api import memcache, taskqueue

my_default_retry_params = gcs.RetryParams(initial_delay=0.2,
                                          max_delay=5.0, backoff_factor=2,
                                          max_retry_period=15)
gcs.set_default_retry_params(my_default_retry_params)


class GenerateReport(pipeline.Pipeline):
    def run(self, settings_key, mode, job_id):
        s = ghidonations.tools.keys.get_key(settings_key).get()

        if mode == "contacts":
            query = s.data.all_contacts
            num_results = 30

        elif mode == "donations":
            query = s.data.all_donations
            num_results = 50

        elif mode == "individuals":
            query = s.data.all_individuals
            num_results = 15

        else:
            raise Exception("Unidentified mode in GenerateReport")

        blobs = []
        cursor = None

        # Create header CSV file
        header_file_name = job_id + "-0.csv"
        blobs.append((yield HeaderCSV(mode, header_file_name)))

        while True:
            results = util.query_cursor_db(query, cursor, keys_only=True, num_results=num_results)
            keys, cursor = results[0], results[1]
            file_name = job_id + "-" + str(len(blobs)) + ".csv"

            keys = util.ndb_key_to_urlsafe(keys)

            blobs.append((yield CreateCSV(mode, file_name, keys)))

            if not cursor:
                break

        final_file_name = s.name + "-" + mode.title() + ".csv"
        gcs_file_key = yield ConcatCSV(job_id, final_file_name, *blobs)
        yield ConfirmCompletion(job_id, gcs_file_key)


class HeaderCSV(pipeline.Pipeline):
    def run(self, mode, file_name):
        # Open GCS file for writing
        gcs_file_key, gcs_file = spreadsheet.new_file("text/csv", file_name)

        si = cStringIO.StringIO()
        writer = csv.writer(si)

        # Write headers
        header_data = []

        if mode == "contacts":
            header_data.append("Name")
            header_data.append("Total Donated")
            header_data.append("Number Donations")
            header_data.append("Phone")
            header_data.append("Street")
            header_data.append("City")
            header_data.append("State")
            header_data.append("Zipcode")
            header_data.append("Created")
            header_data.append("Email")

        if mode == "donations":
            header_data.append("Date")
            header_data.append("Name")
            header_data.append("Email")
            header_data.append("Amount Donated")
            header_data.append("Payment Type")
            header_data.append("Team")
            header_data.append("Individual")
            header_data.append("Reviewed")
            header_data.append("Phone")
            header_data.append("Street")
            header_data.append("City")
            header_data.append("State")
            header_data.append("Zipcode")

        elif mode == "individuals":
            header_data.append("Name")
            header_data.append("Email")
            header_data.append("Teams")
            header_data.append("Raised")
            header_data.append("Date Created")

        writer.writerow(header_data)

        gcs_file.write(si.getvalue())
        gcs_file.close()

        taskqueue.add(url="/tasks/deletespreadsheet", params={'k': gcs_file_key}, countdown=1800,
                      queue_name="deletespreadsheet")

        return gcs_file_key


class CreateCSV(pipeline.Pipeline):
    def run(self, mode, file_name, keys):
        # Open GCS file for writing
        gcs_file_key, gcs_file = spreadsheet.new_file("text/csv", file_name)

        si = cStringIO.StringIO()
        writer = csv.writer(si)

        for k in keys:
            try:
                e = ghidonations.tools.keys.get_key(k).get()

                row_data = []

                if mode == "contacts":
                    c = e
                    row_data.append(c.name)
                    row_data.append(c.data.donation_total)
                    row_data.append(c.data.number_donations)
                    row_data.append(c.phone)
                    row_data.append(c.address[0])
                    row_data.append(c.address[1])
                    row_data.append(c.address[2])
                    row_data.append(c.address[3])
                    row_data.append(str(c.creation_date))

                    for e in c.email:
                        row_data.append(e)

                elif mode == "donations":
                    d = e
                    c = d.contact.get()
                    row_data.append(str(d.donation_date))
                    row_data.append(d.name)
                    row_data.append(d.given_email)
                    row_data.append(str(d.amount_donated))
                    row_data.append(d.payment_type)
                    row_data.append(d.designated_team)
                    row_data.append(d.designated_individual)
                    row_data.append(str(d.reviewed))
                    row_data.append(c.phone)
                    row_data.append(c.address[0])
                    row_data.append(c.address[1])
                    row_data.append(c.address[2])
                    row_data.append(c.address[3])

                elif mode == "individuals":
                    i = e
                    row_data.append(i.name)
                    row_data.append(i.email)
                    row_data.append(i.data.readable_team_names)
                    row_data.append(str(i.data.donation_total))
                    row_data.append(str(i.creation_date))

                writer.writerow(row_data)

            except Exception, e:
                logging.error("Failed on key " + k + " because " + str(e))

            # Call the garbage handler
            gc.collect()

        gcs_file.write(si.getvalue())
        gcs_file.close()

        taskqueue.add(url="/tasks/deletespreadsheet", params={'k': gcs_file_key}, countdown=1800,
                      queue_name="deletespreadsheet")

        return gcs_file_key


class ConcatCSV(pipeline.Pipeline):
    def run(self, job_id, file_name, *blobs):
        gcs_writer_key, gcs_writer = spreadsheet.new_file("text/csv", file_name)

        for b in blobs:
            gcs_reader = gcs.open(b)
            data = gcs_reader.read()

            gcs_writer.write(data)

            # Call the garbage handler
            gc.collect()

        gcs_writer.close()
        taskqueue.add(url="/tasks/deletespreadsheet", params={'k': gcs_writer_key}, countdown=1800,
                      queue_name="deletespreadsheet")

        return gcs_writer_key


class ConfirmCompletion(pipeline.Pipeline):
    def run(self, job_id, gcs_file_key):
        memcache.set(job_id, gcs_file_key)
