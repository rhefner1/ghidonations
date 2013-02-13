#App engine platform
import logging, webapp2, appengine_config

import GlobalUtilities as tools
import DataModels as models

from google.appengine.api import mail
from google.appengine.ext.webapp import template
        
class Confirmation(webapp2.RequestHandler):
    def post(self):
        donation_key = self.request.get("donation_key")
        d = tools.getKey(donation_key).get()

        logging.info("Retrying confirmation email through task queue for donation: " + donation_key)
        
        d.confirmation.email()

class MailchimpAdd(webapp2.RequestHandler):
    def post(self):
        email = self.request.get("email")
        name = self.request.get("name")

        settings_key = self.request.get("settings")
        s = tools.getKey(settings_key).get()

        s.mailchimp.add(email, name, True)

        logging.info("Retrying Mailchimp add through task queue for: " + email  + " under settings ID: " + settings_key)

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

class IndexAll(webapp2.RequestHandler):
    def post(self):
        settings_key = self.request.get("settings_key")
        key = tools.getKey(settings_key)

        mode = self.request.get("mode")

        if mode == "contacts":
            contacts = models.Contact.gql("WHERE settings = :s", s=key)
            for c in contacts:
                c.search.index()

        elif mode == "deposits":
            deposits = models.DepositReceipt.gql("WHERE settings = :s", s=key)
            for de in deposits:
                de.search.index()

        elif mode == "donations":
            donations = models.Donation.gql("WHERE settings = :s", s=key)
            for d in donations:
                d.search.index()

        elif mode == "individuals":
            individuals = models.Individual.gql("WHERE settings = :s", s=key)
            for i in individuals:
                i.search.index()

        elif mode == "teams":
            teams = models.Team.gql("WHERE settings = :s", s=key)
            for t in teams:
                t.search.index()

app = webapp2.WSGIApplication([
       ('/tasks/confirmation', Confirmation),
       ('/tasks/annualreport', AnnualReport),
       ('/tasks/indexall', IndexAll),
       ('/tasks/mailchimp', MailchimpAdd)],
       debug=True)
app = appengine_config.recording_add_wsgi_middleware(app)
