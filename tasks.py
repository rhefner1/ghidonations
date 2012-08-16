#App engine platform
import logging, webapp2, appengine_config

import GlobalUtilities as tools
import DataModels as models
        
class Confirmation(webapp2.RequestHandler):
    def post(self):
        donation_key = self.request.get("donation_key")
        d = tools.getKey(donation_key).get()

        logging.info("Retrying confirmation email through task queue for donation: " + donation_key)
        
        d.confirmation.email()

class MailchimpAdd(webapp2.RequestHandler):
    def post(self):
        email = self.request.get("email")
        settings_key = self.request.get("settings")
        s = tools.getKey(settings_key).get()

        logging.info("Retrying Mailchimp add through task queue for: " + email  + " under settings ID: " + settings_key)

        s.mailchimp.add(email,True)


app = webapp2.WSGIApplication([
       ('/tasks/confirmation', Confirmation),
       ('/tasks/mailchimp', MailchimpAdd)],
       debug=True)
app = appengine_config.recording_add_wsgi_middleware(app)
