# App Engine platform
import logging, csv, gc
from google.appengine.ext import blobstore
from google.appengine.api import files, memcache, taskqueue

# Application files
import DataModels as models
import GlobalUtilities as tools

# Pipeline API
import pipeline
from pipeline import common

class GenerateReport(pipeline.Pipeline):
	def run(self, settings_key, mode, job_id):
		s = tools.getKey(settings_key).get()

		if mode == "contacts":
			query = s.data.all_contacts

		elif mode == "donations":
			query = s.data.all_donations

		elif mode == "individuals":
			query = s.data.all_individuals

		else:
			raise Exception("Unidentified mode in GenerateReport")
		
		blobs = []
		cursor = None

		# Create header CSV file
		header_file_name = job_id + "-0.csv"
		blobs.append( (yield HeaderCSV(mode, header_file_name)) )

		while True:
			results = tools.queryCursorDB(query, cursor, keys_only=True, num_results=50)
			keys, cursor = results[0], results[1]
			file_name = job_id + "-" + str( len(blobs) ) + ".csv"

			keys = tools.ndbKeyToUrlsafe(keys)

			blobs.append( (yield CreateCSV(mode, file_name, keys)) )

			if cursor == None:
				break

		final_file_name = s.name + "-" + mode.title() + ".csv"
		final_blob = yield ConcatCSV(job_id, final_file_name, *blobs)
		yield ConfirmCompletion(job_id, final_blob)

class HeaderCSV(pipeline.Pipeline):
	def run(self, mode, file_name):
		file_key = tools.newFile("text/csv", file_name)

		with files.open(file_key, 'a') as f:
			writer = csv.writer(f)

			# Write headers
			header_data = []

			if mode == "contacts":
				header_data.append("Name")
				header_data.append("Email")
				header_data.append("Total Donated")
				header_data.append("Number Donations")
				header_data.append("Phone")
				header_data.append("Street")
				header_data.append("City")
				header_data.append("State")
				header_data.append("Zipcode")
				header_data.append("Created")

			if mode == "donations":
				header_data.append("Date")
				header_data.append("Name")
				header_data.append("Email")
				header_data.append("Amount Donated")
				header_data.append("Payment Type")
				header_data.append("Team")
				header_data.append("Individual")
				header_data.append("Reviewed")

			elif mode == "individuals":
				header_data.append("Name")
				header_data.append("Email")
				header_data.append("Teams")
				header_data.append("Raised")
				header_data.append("Date Created")

			writer.writerow(header_data)

		files.finalize(file_key)
		blob_key = str(files.blobstore.get_blob_key(file_key))

		taskqueue.add(url="/tasks/deletespreadsheet", params={'k':blob_key}, countdown=3600, queue_name="deletespreadsheet")

		return blob_key

class CreateCSV(pipeline.Pipeline):
	def run(self, mode, file_name, keys):
		file_key = tools.newFile("text/csv", file_name)

		with files.open(file_key, 'a') as f:
			writer = csv.writer(f)

			for k in keys:
				try:
					e = tools.getKey(k).get()

					row_data = []

					if mode == "contacts":
						c = e
						row_data.append(c.name)
						row_data.append(c.email)
						row_data.append(c.data.donation_total)
						row_data.append(c.data.number_donations)
						row_data.append(c.phone)
						row_data.append(c.address[0])
						row_data.append(c.address[1])
						row_data.append(c.address[2])
						row_data.append(c.address[3])
						row_data.append(str(c.creation_date))

					elif mode == "donations":
						d = e
						row_data.append(str(d.donation_date))
						row_data.append(d.name)
						row_data.append(d.email)
						row_data.append(str(d.amount_donated))
						row_data.append(d.payment_type)
						row_data.append(d.designated_team)
						row_data.append(d.designated_individual)
						row_data.append(str(d.reviewed))

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

		files.finalize(file_key)
		blob_key = str(files.blobstore.get_blob_key(file_key))

		taskqueue.add(url="/tasks/deletespreadsheet", params={'k':blob_key}, countdown=3600, queue_name="deletespreadsheet")

		return blob_key
		
class ConcatCSV(pipeline.Pipeline):
	def run(self, job_id, file_name, *blobs):
		file_key = tools.newFile("text/csv", file_name)

		with files.open(file_key, 'a') as f:

			for b in blobs:
				blob_reader = blobstore.BlobReader(b)
				value = blob_reader.read()

				f.write(value)

				# Call the garbage handler
				gc.collect()

		files.finalize(file_key)
		blob_key = str(files.blobstore.get_blob_key(file_key))

		taskqueue.add(url="/tasks/deletespreadsheet", params={'k':blob_key}, countdown=3600, queue_name="deletespreadsheet")

		return blob_key

class ConfirmCompletion(pipeline.Pipeline):
	def run(self, job_id, final_blob):
		memcache.set(job_id, final_blob)