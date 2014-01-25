#App engine platform
import logging, webapp2, appengine_config, json, gc

import GlobalUtilities as tools
import DataModels as models

from google.appengine.api import mail, taskqueue, files, memcache
from google.appengine.ext import deferred, blobstore
from google.appengine.ext.webapp import template
from datetime import datetime, timedelta

#Excel export
from xlwt import *

# Google Cloud Storage
import cloudstorage as gcs

class AggregateAnnualReport(webapp2.RequestHandler):
    def post(self):
        target_year = int(self.request.get("year"))
        s = tools.getKey( self.request.get("skey") )
        mode = self.request.get("mode")

        td1 = datetime(target_year,1,1,0,0)
        td2 = datetime(target_year,12,31,0,0)

        annual_donations = models.Donation.query(models.Donation.settings == s, 
                                                models.Donation.donation_date >= td1,
                                                models.Donation.donation_date <= td2)

        all_contacts = set([d.contact for d in annual_donations])

        with_email = []
        without_email = []
        missing_contacts = []

        for c_key in all_contacts:
            c = c_key.get()
            if not c:
                missing_contacts.append(c_key)

            else:

                if c.email != ['']:
                    with_email.append(c)

                else:
                    donation_total = c.data.donation_total
                    if donation_total >= tools.toDecimal("250"):
                        without_email.append(c)

                    elif c.data.number_donations == 1 and donation_total >= tools.toDecimal("100"):
                        without_email.append(c)

        body = ""

        body += "\n" + "#### " + str(len(with_email)) + " Donors with Email Addresses ####"
        for c in with_email:
            body += "\n" + str(c.key)

        body += "\n" + "\n\n\n#### " + str(len(without_email)) + " Donors WITHOUT Email Addresses ####"
        for c in without_email:
            body += "\n" + "https://ghidonations.appspot.com/reports/donor?c=" + c.websafe + "&y=2013"

        body += "\n" + "\n\n\n#### " + str(len(missing_contacts)) + " Missing Contacts ####"
        for c in missing_contacts:
            body += "\n" + str(c)

        # Writing text file
        gcs_file_key, gcs_file = tools.newFile("text/plain", "GHI_Donations_" + str(target_year) + ".txt")
        gcs_file.write( body )
        gcs_file.close()


class AnnualReport(webapp2.RequestHandler):
    def post(self):
        contact_key = self.request.get("contact_key")
        year = self.request.get("year")
        c = tools.getKey(contact_key).get()

        logging.info("AnnualReport handler hit with contact key " + contact_key + " and year " + year)

        if c.email:

            message = mail.EmailMessage()
            message.to = c.email
            message.sender = "Global Hope India <donate@globalhopeindia.org>"
            message.subject = "2012 Global Hope India Donations"

            donations = c.data.annual_donations(year)
            donation_total = tools.toDecimal(0)

            for d in donations:
                donation_total += d.confirmation_amount

            donation_total = "${:,.2f}".format(donation_total)

            template_variables = {"s":c.settings.get(), "c":c, "donations":donations, "year":year, "donation_total":str(donation_total)}

            message.html = template.render("pages/letters/donor_report.html", template_variables)
            message.send()

            logging.info("Annual report sent to:" + c.name)

        else:
            logging.info("Annual report not sent sent because " + c.name + "doesn't have an email.")
        
class Confirmation(webapp2.RequestHandler):
    def post(self):
        donation_key = self.request.get("donation_key")
        d = tools.getKey(donation_key).get()

        logging.info("Retrying confirmation email through task queue for donation: " + donation_key)
        
        d.confirmation.email()

class DelayIndexing(webapp2.RequestHandler):
    def post(self):
        entity_key = self.request.get("e")

        try:
            e = tools.getKey(entity_key).get()
            e.search.index()
        except Exception, e:
            logging.error( str(e) )
            self.error(500)

class DeleteSpreadsheet(webapp2.RequestHandler):
    def post(self):
        file_key = self.request.get("k")

        try:
            gcs.delete(file_key)
        except:
            pass

class IndexAll(webapp2.RequestHandler):
    def post(self):
        mode = self.request.get("mode")

        if mode == "contacts":
            contacts = models.Contact.query()
            deferred.defer(tools.indexEntitiesFromQuery, contacts, _queue="backend")

        elif mode == "deposits":
            deposits = models.DepositReceipt.query()
            deferred.defer(tools.indexEntitiesFromQuery, deposits, _queue="backend")

        elif mode == "donations":
            donations = models.Donation.query()
            deferred.defer(tools.indexEntitiesFromQuery, donations, _queue="backend")

        elif mode == "individuals":
            individuals = models.Individual.query()
            deferred.defer(tools.indexEntitiesFromQuery, individuals, _queue="backend")

        elif mode == "teams":
            teams = models.Team.query()
            deferred.defer(tools.indexEntitiesFromQuery, teams, _queue="backend")

class MailchimpAdd(webapp2.RequestHandler):
    def post(self):
        email = self.request.get("email")
        name = self.request.get("name")

        settings_key = self.request.get("settings")
        s = tools.getKey(settings_key).get()

        s.mailchimp.add(email, name, True)

        logging.info("Retrying Mailchimp add through task queue for: " + email  + " under settings ID: " + settings_key)

class ReindexEntities(webapp2.RequestHandler):
    def post(self):
        mode = self.request.get("mode")
        e_key = self.request.get("key")

        base = tools.getKey(e_key).get()

        if mode == "contact":
            query = models.Donation.query(models.Donation.settings == base.settings, models.Donation.contact == base.key)
            query = tools.qCache(query)

        elif mode == "individual":
            query = base.data.donations

        elif mode == "team":
            query = base.data.donations

        for e in query:
            taskqueue.add(url="/tasks/delayindexing", params={'e' : e.key.urlsafe()}, countdown=2, queue_name="delayindexing")

class UpdateAnalytics(webapp2.RequestHandler):
    def _run(self):

        #Scheduled cron job to update analytics for all settings accounts every hour
        all_settings = models.Settings.query()
        for s in all_settings:

            ## Update one_week_history
            last_week = datetime.today() - timedelta(days=7)

            #Get donations made in the last week
            donations = models.Donation.gql("WHERE settings = :s AND donation_date > :last_week ORDER BY donation_date DESC", 
                        s=s.key, last_week=last_week)

            donation_count = 0
            total_money = tools.toDecimal(0)

            for d in donations:
                #Counting total money
                total_money += d.amount_donated
                
                #Counting number of donations
                donation_count += 1

            one_week_history = [donation_count, str(total_money)]
            s.one_week_history = json.dumps(one_week_history)

            #####################################################################################################

            ## Update one_month_history
            last_week = datetime.today() - timedelta(days=30)

            #Get donations made in the last week
            donations = models.Donation.gql("WHERE settings = :s AND donation_date > :last_week ORDER BY donation_date DESC", 
                        s=s.key, last_week=last_week)

            one_month_history = [["Date", "Amount Donated ($)"]]
            donations_dict = {}

            for d in donations:
                d_date = tools.convertTime(d.donation_date)
                day = str(d_date.month).zfill(2) + "/" + str(d_date.day).zfill(2)

                if day in donations_dict:
                    donations_dict[day] += d.amount_donated
                else:
                    donations_dict[day] = d.amount_donated

            for date in sorted(donations_dict.iterkeys()):
                one_month_history.append([date, float(donations_dict[date])])

            s.one_month_history = json.dumps(one_month_history)

            s.put()

    get = post = _run

class UpdateContactsJSON(webapp2.RequestHandler):
    def post(self):
        s_key = self.request.get("s_key")
        s = tools.getKey(s_key).get()

        contacts = []

        for c in s.data.all_contacts:
            contact = {}
            contact["label"] = c.name
            contact["email"] = c.email
            contact["address"] = json.dumps(c.address)
            contact["key"] = str(c.websafe)
            
            contacts.append(contact)
  
        s.contacts_json = json.dumps(contacts)
        s.put()

app = webapp2.WSGIApplication([
        ('/tasks/annualreport', AnnualReport),
        ('/tasks/aggregateannualreport', AggregateAnnualReport),
        ('/tasks/confirmation', Confirmation),
        ('/tasks/delayindexing', DelayIndexing),
        ('/tasks/deletespreadsheet', DeleteSpreadsheet),
        ('/tasks/indexall', IndexAll),
        ('/tasks/mailchimp', MailchimpAdd),
        ('/tasks/reindex', ReindexEntities),

        ('/tasks/updateanalytics', UpdateAnalytics),
        ('/tasks/contactsjson', UpdateContactsJSON)],
        debug=True)
app = appengine_config.recording_add_wsgi_middleware(app)
