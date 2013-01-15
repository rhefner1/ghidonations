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
                donation_total += d.amount_donated

            donation_total = "${:,.2f}".format(donation_total)

            template_variables = {"s":c.settings.get(), "c":c, "donations":donations, "year":year, "donation_total":str(donation_total)}

            message.html = template.render("pages/letters/donor_report.html", template_variables)
            message.send()

            logging.info("Annual report sent to:" + c.name)

        else:
            logging.info("Annual report not sent sent because " + c.name + "doesn't have an email.")


app = webapp2.WSGIApplication([
       ('/tasks/confirmation', Confirmation),
       ('/tasks/annualreport', AnnualReport),
       ('/tasks/mailchimp', MailchimpAdd)],
       debug=True)
app = appengine_config.recording_add_wsgi_middleware(app)
