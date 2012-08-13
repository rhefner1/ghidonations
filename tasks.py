import logging

#App engine platform
import wsgiref.handlers
from google.appengine.ext.webapp.util import run_wsgi_app
import webapp2 as webapp

import GlobalUtilities as tools
import DataModels as models

import appengine_config
        
class Confirmation(webapp.RequestHandler):
    def post(self):
        donation_key = self.request.get("donation_key")
        d = tools.getKey(donation_key).get()

        logging.info("Retrying confirmation email through task queue for donation: " + donation_key)
        
        d.confirmation.email()

class MailchimpAdd(webapp.RequestHandler):
    def post(self):
        email = self.request.get("email")
        settings_key = self.request.get("settings")
        s = tools.getKey(settings_key).get()

        logging.info("Retrying Mailchimp add through task queue for: " + email  + " under settings ID: " + settings_key)

        s.mailchimp.add(email,True)


app = webapp.WSGIApplication([
       ('/tasks/confirmation', Confirmation),
       ('/tasks/utility', UtilityTask),
       ('/tasks/mailchimp', MailchimpAdd)],
       debug=True)
app = appengine_config.recording_add_wsgi_middleware(app)
