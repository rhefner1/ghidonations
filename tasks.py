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

class ConvertKeys(webapp.RequestHandler):
    def post(self):
        # Dev
        # master_settings = tools.getKey("ahBkZXZ-Z2hpZG9uYXRpb25zchALEghTZXR0aW5ncxiZ7AMM").get()

        #Production
        master_settings = tools.getKey("ag5zfmdoaWRvbmF0aW9uc3IQCxIIU2V0dGluZ3MYmewDDA").get()

        all_settings = models.Settings.query()
        all_individuals = models.Individual.query()
        all_teams = models.Team.query()
        all_deposits = models.DepositReceipt.query()
        all_contacts = models.Contact.query()
        all_donations = models.Donation.query()

        all_tl = models.TeamList.query()
        for t in all_tl:
            t.key.delete()
            
        for i in all_individuals:

            if i.settings_key:
                i.settings = ndb.Key(urlsafe=i.settings_key)

            team_list = json.loads(i.team_list)

            for k in team_list:
                team_key = k

                new_it = models.TeamList()
                new_it.individual = i.key
                new_it.team = tools.getKey(team_key)
                try:
                    new_it.fundraise_amt = tools.toDecimal(team_list[k][1])
                except:
                    new_it.fundraise_amt = tools.toDecimal(20)

                new_it.put()

            try:
                del i.history
            except:
                pass

            i.put()
        for t in all_teams:
            if t.settings_key:
                t.settings = ndb.Key(urlsafe=t.settings_key)

            try:
                del t.history
            except:
                pass

            t.put()
        for d in all_deposits:
            if d.settings_key:
                d.settings = ndb.Key(urlsafe=d.settings_key)

            new_list = []
            for e in d.entity_keys:
                if isinstance(e, (str)):
                    new_list.append(ndb.Key(urlsafe=e))
                else:
                    new_list.append(e)
            d.entity_keys = new_list

            d.put()
        for c in all_contacts:
            try:
                if c.settings_key:
                    c.settings = ndb.Key(urlsafe=c.settings_key)
            except:
                pass

            if c.address != 'None' and c.address != None:
                try:
                    new_address = json.loads(str(c.address))

                except Exception as e:
                    logging.info("Address fail: " + str(e))
                    new_address = ['', '', '', '']
            else:
                logging.info("Address equals none.")
                new_address = ['', '', '', '']
                
            c.address = new_address

            try:
                c.put()
            except Exception as e:
                logging.info("FAIL: Contact put - " + c.name + " because " + str(e))

        for d in all_donations:
            try:
                if d.team:
                    d.team = ndb.Key(urlsafe=d.team)
            except Exception as e:
                logging.info("Team assign fail: " + str(e))
                
            try:
                if d.individual:
                    d.individual = ndb.Key(urlsafe=d.individual)
            except Exception as e:
                logging.info("Individual assign fail: " + str(e))

            try:
                if d.settings_key:
                    d.settings = ndb.Key(urlsafe=d.settings_key)
            except Exception as e:
                logging.info("Settings assign fail: " + str(e))

            d.given_name = d.name
            d.given_email = d.email

            query = models.Contact.gql("WHERE name = :n", n=d.name)
            try:
                d.contact = query.fetch(1)[0].key
            except Exception as e:
                logging.info("FAIL: Donation contact - " + d.name + " because " + str(e))
                s = master_settings
                d.contact = s.create.contact(d.name, d.email, None, None, None, False)

            try:
                del d.history
            except:
                pass

            d.put()

        logging.info("DONE WITH KEY CONVERSION")

app = webapp.WSGIApplication([
       ('/tasks/delaypayment', DelayPayment),
       ('/tasks/confirmation', Confirmation),
       ('/tasks/convertkeys', ConvertKeys),
       ('/tasks/mailchimp', MailchimpAdd)],
       debug=True)
app = appengine_config.recording_add_wsgi_middleware(app)
