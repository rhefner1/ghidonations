#App engine platform
import logging, webapp2, appengine_config, json

import GlobalUtilities as tools
import DataModels as models

from google.appengine.api import mail, taskqueue
from google.appengine.ext.webapp import template
from datetime import datetime, timedelta

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
        except:
            self.error(500)

class IndexAll(webapp2.RequestHandler):
    def post(self):
        mode = self.request.get("mode")

        if mode == "contacts":
            contacts = models.Contact.query()
            for c in contacts.iter(keys_only=True):
                taskqueue.add(url="/tasks/delayindexing", params={'e' : c.urlsafe()}, queue_name="delayindexing")

        elif mode == "deposits":
            deposits = models.DepositReceipt.query()
            for de in deposits.iter(keys_only=True):
                taskqueue.add(url="/tasks/delayindexing", params={'e' : de.urlsafe()}, queue_name="delayindexing")

        elif mode == "donations":
            donations = models.Donation.query()
            for d in donations.iter(keys_only=True):
                taskqueue.add(url="/tasks/delayindexing", params={'e' : d.urlsafe()}, queue_name="delayindexing")

        elif mode == "individuals":
            individuals = models.Individual.query()
            for i in individuals.iter(keys_only=True):
                taskqueue.add(url="/tasks/delayindexing", params={'e' : i.urlsafe()}, queue_name="delayindexing")

        elif mode == "teams":
            teams = models.Team.query()
            for t in teams.iter(keys_only=True):
                taskqueue.add(url="/tasks/delayindexing", params={'e' : t.urlsafe()}, queue_name="delayindexing")

class MailchimpAdd(webapp2.RequestHandler):
    def post(self):
        email = self.request.get("email")
        name = self.request.get("name")

        settings_key = self.request.get("settings")
        s = tools.getKey(settings_key).get()

        s.mailchimp.add(email, name, True)

        logging.info("Retrying Mailchimp add through task queue for: " + email  + " under settings ID: " + settings_key)

class UpdateAnalytics(webapp2.RequestHandler):
    def post(self):

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
                day = str(d.donation_date.month).zfill(2) + "/" + str(d.donation_date.day).zfill(2)

                if day in donations_dict:
                    donations_dict[day] += d.amount_donated
                else:
                    donations_dict[day] = d.amount_donated

            for date in sorted(donations_dict.iterkeys()):
                one_month_history.append([date, float(donations_dict[date])])

            s.one_month_history = json.dumps(one_month_history)

            s.put()

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
        ('/tasks/confirmation', Confirmation),
        ('/tasks/contactsjson', UpdateContactsJSON),
        ('/tasks/delayindexing', DelayIndexing),
        ('/tasks/indexall', IndexAll),
        ('/tasks/mailchimp', MailchimpAdd),
        ('/tasks/updateanalytics', UpdateAnalytics)],
        debug=True)
app = appengine_config.recording_add_wsgi_middleware(app)
