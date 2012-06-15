import logging

#App engine platform
import wsgiref.handlers
from google.appengine.ext.webapp.util import run_wsgi_app
import webapp2 as webapp

import GlobalUtilities as tools
import DataModels as models

import appengine_config

import json, datetime, time   
from decimal import *

#Images API and taskqueue
from google.appengine.api import images, taskqueue

#Database and deferred tasks
from google.appengine.ext import ndb, deferred

class DelayPayment(webapp.RequestHandler):
    def post(self):
        payment_id = self.request.get("payment_id")
        amount_donated = self.request.get("amount_donated")
        
        logging.info("Retrying recurring payment: " + payment_id + " for $" + amount_donated)

        tools.addRecurringDonation(self, payment_id, amount_donated, True)
        
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

class UtilityTask(webapp.RequestHandler):
    def post(self):
        all_d = models.Donation.query()
        for d in all_d:
            if not d.confirmation_amount:
                d.confirmation_amount = d.amount_donated
                d.put()


app = webapp.WSGIApplication([
       ('/tasks/delaypayment', DelayPayment),
       ('/tasks/confirmation', Confirmation),
       ('/tasks/utility', UtilityTask),
       ('/tasks/mailchimp', MailchimpAdd)],
       debug=True)
app = appengine_config.recording_add_wsgi_middleware(app)
