# coding: utf-8
import webapp2 as webapp
from google.appengine.ext.webapp import template

import logging, json, datetime, time   
from decimal import *

#Images API and taskqueue
from google.appengine.api import images, taskqueue

#Database and deferred tasks
from google.appengine.ext import ndb, deferred    

import appengine_config

import GlobalUtilities as tools
import DataModels as models

class RPCHandler(webapp.RequestHandler):
    def __init__(self, request, response):
        self.initialize(request, response)
        self.methods = RPCMethods()

    def get(self):
        self.response.headers['Access-Control-Allow-Origin'] = '*'
        authenticated = tools.RPCcheckAuthentication(self, True)
        #authenticated = True

        func = None
        action = self.request.get('action')

        if action:
            logging.info("Action: " + str(action))

            if action[0] == '_':
                self.error(403) # access denied
                return

            elif action[0:4] == 'pub_':
                func = getattr(self.methods, action, None)

            elif action[0:5] == "semi_":
                if authenticated == "semi" or authenticated == True:
                    func = getattr(self.methods, action, None)
                else:
                    self.error(401)
                    self.response.out.write("I'm not authorized to give you that information until you log in. Sorry!")

            else:
                if authenticated == True:
                    func = getattr(self.methods, action, None)
                else:
                    self.error(401)
                    self.response.out.write("I'm not authorized to give you that information until you log in. Sorry!")


        if not func:
            self.error(404) # method not found
            return

        args = ()
        while True:
            key = 'arg%d' % len(args)
            val = self.request.get(key)
            if val:
                args += (json.loads(val),)
            else:
                break

        result = func(*args)
        dthandler = lambda obj: obj.isoformat() if isinstance(obj, datetime.datetime) else None
        self.response.out.write(json.dumps(result, default=dthandler))
    
    def post(self):
        self.response.headers['Access-Control-Allow-Origin'] = '*'
        authenticated = tools.RPCcheckAuthentication(self, True)

        args = json.loads(self.request.body)
        func, args = args[0], args[1:]

        if func[0] == '_':
            self.error(403) # access denied
            return

        elif func[0:4] == "pub_":
            func = getattr(self.methods, func, None)

        elif func[0:5] == "semi_":
            if authenticated == "semi" or authenticated == True:
                func = getattr(self.methods, func, None)
            else:
                self.error(401)
                self.response.out.write("I'm not authorized to give you that information until you log in. Sorry!")

        else:
            if authenticated == True:
                func = getattr(self.methods, func, None)
            else:
                self.error(401)
                self.response.out.write("I'm not authorized to give you that information until you log in. Sorry!")

        if not func:
            self.error(404) # file not found
            return

        result = func(*args)
        self.response.out.write(json.dumps(result))
   
## -- Set of functions that returns data to above GET request -- ##
class RPCMethods:
    # Every function here gives a success/fail and a response.
    # Even though there's no response needed, we have to return
    # something so it integrates with other functions
    # that do have a value to return. The response in that case is None

#### ---- TEMPORARY TEST FUNCTIONS - SHOULD BE HIDDEN ON PRODUCTION RELEASE ---- ####

    def totalMoney(self):
        donations = models.Donation.query()
        amount = tools.toDecimal(0)

        for d in donations:
            amount += d.amount_donated
        
        return "Total amount donated: " + str(amount)

    def pub_sandboxSettings(self):
        name = "Testing"
        email = "tester@example.com"
        settings = tools.newSettings(self, name, email)

        return settings.urlsafe()

    def saveDatastore(self):
        from google.appengine.tools import dev_appserver 
        dev_appserver.TearDownStubs()
        return "Datastore Saved!"

    def pub_refreshSandbox(self):
        #Local SDK
        settings = "ahBkZXZ-Z2hpZG9uYXRpb25zcg4LEghTZXR0aW5ncxgBDA"

        #Production
        # settings = "ag5zfmdoaWRvbmF0aW9uc3IQCxIIU2V0dGluZ3MY9dIWDA"

        s = tools.getKey(settings).get()

        s.name = "Testing"
        s.email = "test@example.com"
        s.mc_use = False
        s.mc_apikey = None
        s.mc_donorlist = None
        s.impressions = []
        s.paypal_id = "test@example.com"
        s.amount1 = 25
        s.amount2 = 50
        s.amount3 = 75
        s.amount4 = 100
        s.use_custom = True
        s.confirmation_text = ""
        s.confirmation_info = ""
        s.confirmation_header = ""
        s.confirmation_footer = ""
        s.wp_url = None
        s.wp_username = None
        s.wp_password = None

        s.put()

        for i in s.data.all_individuals:
            i.key.delete()
        for t in s.data.all_teams:
            t.key.delete()
        for d in s.data.all_deposits:
            d.key.delete()
        for c in s.data.all_contacts:
            for i in c.data.all_impressions:
                i.key.delete()
            c.key.delete()
        for d in s.data.all_donations:
            d.key.delete()

        team_key = s.create.team("Cool Group")

        s.create.individual("Tester", team_key, "test@example.com", "ghi", True)
        s.create.individual("Ryan Hefner", team_key, "rhefner1@gmail.com", "ghi", True)

        s.create.contact("Sandra Baker", "sbaker@example.com", "9199858383", None, "Sandra is great!", False)
        s.create.contact("James Bonner", "jbonner@example.com", "9195682254", None, None, False)
        s.create.contact("James Winchester", "jwinchester@example.com", None, None, None, False)
        s.create.contact("Clayton Joslin", "cjoslin@example.com", None, None, None, False)
        s.create.contact("Robert Roberson", "rroberson@example.com", None, None, None, False)
        s.create.contact("Thomas Dodge", "tdodge@example.com", None, None, None, False)
        s.create.contact("Colleen Molina", "cmolina@example.com", None, None, None, False)
        s.create.contact("Rachel Sanders", "rsanders@example.com", None, None, None, False)
        s.create.contact("Jason Tinsley", "jtinsley@example.com", None, None, None, False)
        s.create.contact("Christopher Walker", "cwalker@example.com", None, None, None, False)
        s.create.contact("Evelyn Newsome", "enewsome@example.com", None, None, None, False)
        s.create.contact("Jenny McGinty", "jmcginty@example.com", None, None, None, False)
        s.create.contact("Sara Ruiz", "sruiz@example.com", None, None, None, False)
        s.create.contact("Curtis Smalls", "csmalls@example.com", None, None, None, False)
        s.create.contact("Constance Weekley", "cweekley@example.com", None, None, None, False)

        s.create.donation("Sandra Baker", "sbaker@example.com", "12.34", "12.34", None, None, None, True, None, None, "offline", False, None)
        s.create.donation("Sandra Baker", "sbaker@example.com", "1425.25", "1425.25", None, None, None, True, None, None, "offline", False, None)
        s.create.donation("Sandra Baker", "sbaker@example.com", "2346.52", "2346.52", None, None, None, True, None, None, "offline", True, None)
        s.create.donation("Colleen Molina", "cmolina@example.com", "27.50", "27.50", None, None, None, True, None, None, "offline", False, None)
        s.create.donation("Colleen Molina", "cmolina@example.com", "77.50", "77.50", None, None, None, True, None, None, "offline", False, None)
        s.create.donation("Sara Ruiz", "sruiz@example.com", "500.00", "500.00", None, None, None, True, None, None, "offline", False, None)
        s.create.donation("Sara Ruiz", "sruiz@example.com", "700.00", "700.00", None, None, None, True, None, None, "offline", False, None)
        s.create.donation("Constance Weekley", "cweekley@example.com", "1000.00", "1000.00", None, None, None, True, None, None, "offline", False, None)
        s.create.donation("Constance Weekley", "cweekley@example.com", "6000.00", "6000.00", None, None, None, True, None, None, "offline", False, None)

        tools.flushMemcache(self)
        return "Success"

    def flushMemcache(self):
        tools.flushMemcache(self)
        return "Memcache flushed."

    def repaircontacts(self):
        all_d = models.Donation.query()
        for d in all_d:
            c = d.contact.get()
            email = c.email

            if email == None or email == "":
                c.email = d.given_email
            c.put()

    def setConfAmount(self):
        taskqueue.add(url="/tasks/utility", queue_name="backend", params={})

#### ---- Globalhopeindia.org Utility Functions ---- ####
    def individualExists(self, email):
        settings = tools.getSettingsKey(self)
        return settings.get().exists.individual(email)

    def pub_allTeams(self, settings):
    # This returns a json list of teams
        s = tools.getKey(settings).get()

        all_teams = []
        for t in s.data.display_teams:
            team = [t.name, t.key.urlsafe()]           
            all_teams.append(team)
        
        return all_teams

    def pub_teamInfo(self, team_key):
    # This returns a simplejson list of team members' names, hosted link to picture, and description
    # Response parsed by Javascript on main GHI site
        t = tools.getKey(team_key).get()
        return t.data.members_list

    def pub_individualInfo(self, team_key, individual_key):
        i = tools.getKey(individual_key).get()
        t_key = tools.getKey(team_key)
        return i.data.info(t_key)

#### ---- Data Access ---- ####
    def semi_getTeamMembers(self, team_key):
    # Returns team information
        t = tools.getKey(team_key).get()
        return t.data.members_dict

    def IndividualName(self, individual_key):
        i = tools.getKey(individual_key).get()
        return individual.name

    def getSettings(self):
        settings = tools.getAccountEmails(self)
        return settings

    def getTeamDonors(self, team_key):
        s = tools.getSettingsKey(self).get()
        team_key = tools.getKey("ahBkZXZ-Z2hpZG9uYXRpb25zcgoLEgRUZWFtGAIM")
        return s.data.team_donors(team_key)

    def getDonations(self, query_cursor, donation_type):
        s = tools.getSettingsKey(self).get()

        if donation_type == "unreviewed":
            response = s.data.open_donations(query_cursor)

        elif donation_type == "all_donations":
            response = s.data.donations(query_cursor)

        donations = []
        new_cursor = response[1]

        for d in response[0]:
            d_dict = {"key" : d.key.urlsafe(), "formatted_donation_date" : d.formatted_donation_date, "name" : d.name, "email" : d.email,
                 "payment_type" : d.payment_type, "amount_donated" : str(d.amount_donated)}

            donations.append(d_dict)

        #Return message to confirm 
        return_vals = [donations, new_cursor]
        return return_vals

    def getTeams(self, query_cursor):
        s = tools.getSettingsKey(self).get()

        response = s.data.teams(query_cursor)
        teams = []

        for t in response[0]:
            tdict = {"key" : t.websafe, "name" : t.name}
            teams.append(tdict)
        new_cursor = response[1]

        #Return message to confirm 
        return_vals = [teams, new_cursor]
        return return_vals

    def getDeposits(self, query_cursor):
        s = tools.getSettingsKey(self).get()
        response = s.data.deposits(query_cursor)

        deposits = []
        new_cursor = response[1]

        for d in response[0]:
            ddict = {"key" : d.websafe, "time_deposited" : d.time_deposited}
            deposits.append(ddict)

        # #Return message to confirm 
        return_vals = [deposits, new_cursor]
        return return_vals

    def getContacts(self, query_cursor):
        s = tools.getSettingsKey(self).get()

        response = s.data.contacts(query_cursor)

        contacts = tools.GQLtoDict(self, response[0])
        new_cursor = response[1]

        #Return message to confirm 
        return_vals = [contacts, new_cursor]
        return return_vals

    def getIndividuals(self, query_cursor):
        s = tools.getSettingsKey(self).get()

        response = s.data.individuals(query_cursor)

        contacts = tools.GQLtoDict(self, response[0])
        new_cursor = response[1]

        #Return message to confirm 
        return_vals = [contacts, new_cursor]
        return return_vals

    def getContactDonations(self, query_cursor, contact_key):
        c = tools.getKey(contact_key).get()

        response = c.data.donations(query_cursor)

        donations = []
        new_cursor = response[1]

        for d in response[0]:
            d_dict = {"key" : d.key.urlsafe(), "formatted_donation_date" : d.formatted_donation_date, "name" : d.name, "email" : d.email,
                 "payment_type" : d.payment_type, "amount_donated" : str(d.amount_donated)}

            donations.append(d_dict)

        #Return message to confirm 
        return_vals = [donations, new_cursor]
        return return_vals

    def getMailchimpLists(self, mc_apikey):
        return tools.getMailchimpLists(self, mc_apikey)

#### ---- Data creation/updating ---- ####

    def newTeam(self, name):
        message = "<b>" + name + "</b> created"
        success = True

        s = tools.getSettingsKey(self).get()
        s.create.team(name)

        #Return message to confirm 
        return_vals = [success, message]
        return return_vals

    def newIndividual(self, name, team_key, email, password, admin):
        message = "<b>" + name + "</b> created"
        success = True

        s = tools.getSettingsKey(self).get()
        exists = s.exists.individual(email)

        if exists[0] == False:
            if email == "":
                email = None

            if team_key == "team":
                team_key = None

            s.create.individual(name, tools.getKey(team_key), email, password, admin)

        else:
            #If this email address already exists for a user
            message = "Sorry, but this email address is already being used."
            success = False

        #Return message to confirm 
        return_vals = [success, message]
        return return_vals

    def newContact(self, name, email, phone, address, notes):
        message = "<b>" + name + "</b> created"
        success = True

        s = tools.getSettingsKey(self).get()
        contact_exists = s.exists.contact(email)

        address = json.loads(address)

        if contact_exists[0] == False:
            s.create.contact(name, email, phone, address, notes, True)

        else:
            #If this email address already exists for a user
            message = "This contact already exists, but we updated their information."

            c = exists[1].get()
            contact.update(name, email, phone, notes, address)

        #Return message to confirm 
        return_vals = [success, message]
        return return_vals

    def editIndividual(self, name, email, team_list, description):
        message = "Individual saved"
        success = True
        
        i = tools.getKey(individual_key).get()
        i.update(name, email, team_list, description, None)

        #Return message to confirm 
        return_vals = [success, message]
        return return_vals

    def offlineDonation(self, name, email, amount_donated, notes, address, team_key, individual_key, add_deposit):
        message = "Offline donation created"
        success = True

        s = tools.getSettingsKey(self).get()

        if address == "":
            address = None
        else:
            address = json.loads(address)

        if team_key == "" or team_key == "general":
            team_key = None
        else:
            team_key = tools.getKey(team_key)

        if individual_key == "" or individual_key == None:
            individual_key = None
        else:
            individual_key = tools.getKey(individual_key)
            

        s.create.donation(name, email, amount_donated, amount_donated, address, team_key, individual_key, add_deposit, "", "", "offline", False, None)

        #Return message to confirm 
        return_vals = [success, message]
        return return_vals

    def semi_createDonation(self, name, email, amount_donated, notes, address, team_key, individual_key):
        message = "Donation created"
        success = True

        s = tools.getSettingsKey(self).get()

        if team_key == "general":
            team_key = None

        if individual_key == "none":
            individual_key = None

        if notes == None or notes == "":
            notes = "None"
        
        if address == None or address == "":
            address = "None"

        authenticated = tools.RPCcheckAuthentication(self, True)

        if authenticated == "semi":
            notes = "[Offline check entered by team member] - " + notes

        s.create.donation(name, email, amount_donated, amount_donated, address, tools.getKey(team_key), tools.getKey(individual_key), None, None, notes, "team member", False, None)

        #Return message to confirm 
        return_vals = [success, message]
        return return_vals
    
    def updateDonation(self, donation_key, notes, team_key, individual_key, add_deposit):
        message = "Donation has been saved"
        success = True

        d = tools.getKey(donation_key).get()

        if team_key == "general":
            team_key = None
        elif team_key:
            team_key = tools.getKey(team_key)

        if individual_key:
            individual_key = tools.getKey(individual_key)

        d.update(notes, team_key, individual_key, add_deposit)

        #Return message to confirm 
        return_vals = [success, message]
        return return_vals

    def updateContact(self, contact_key, name, email, phone, notes, address):
        message = "Contact has been saved"
        success = True

        c = tools.getKey(contact_key).get()
        address = json.loads(address)
        c.update(name, email, phone, notes, address)
        
        #Return message to confirm 
        return_vals = [success, message]
        return return_vals

    def updateSettings(self, name, email, mc_use, mc_apikey, mc_donorlist, paypal_id, impressions, amount1, amount2, amount3, amount4, use_custom, confirmation_header, confirmation_info, confirmation_footer, confirmation_text, wp_url, wp_username, wp_password):
        message = "Settings have been updated"
        success = True

        s = tools.getSettingsKey(self).get()
        s.update(name, email, mc_use, mc_apikey, mc_donorlist, paypal_id, impressions, amount1, amount2, amount3, amount4, use_custom, confirmation_header, confirmation_info, confirmation_footer, confirmation_text, wp_url, wp_username, wp_password)

        #Return message to confirm 
        return_vals = [success, message]
        return return_vals

    def updateTeam(self, team_key, name, show_team):
        message = "Team has been updated"
        success = True

        t = tools.getKey(team_key).get()
        t.update(name, show_team)

        #Return message to confirm 
        return_vals = [success, message]
        return return_vals

    def donationUnreviewed(self, donation_key):
        message = "Donation marked as unreviewed"
        success = True

        d = tools.getKey(donation_key).get()
        d.review.markUnreviewed()

        #Return message to confirm 
        return_vals = [success, message]
        return return_vals

    def newImpression(self, contact_key, impression, notes):
        message = "Impression saved"
        success = True

        c = tools.getKey(contact_key).get()
        c.create.impression(impression, notes)

        #Return message to confirm 
        return_vals = [success, message]
        return return_vals

#### ---- Search ---- ####
    def getContactsJSON(self):
        s = tools.getSettingsKey(self).get()
        return s.data.contactsJSON

#### ---- Donation depositing ---- ####
    def depositDonations(self, donation_keys):
        message = "Donations deposited."
        success = True

        if donation_keys != []:
            s = tools.getSettingsKey(self).get()
            s.deposits.deposit(donation_keys)

        else:
            message = "No donations to deposit."
            success = False

        #Return message to confirm 
        return_vals = [success, message]
        return return_vals

    def removeFromDeposits(self, donation_keys):
        message = "Donations removed from deposits."
        success = True

        s = tools.getSettingsKey(self).get()

        donation_keys = tools.strArrayToKey(self, donation_keys)
        s.deposits.remove(donation_keys)

        #Return message to confirm 
        return_vals = [success, message]
        return return_vals

#### ---- Confirmation Letters ---- ####
    def emailReceipt(self, donation_key):
        message = "Email sent"
        success = True

        d = tools.getKey(donation_key).get()

        #Email receipt to donor
        d.review.archive()
        d.confirmation.task(60)

        #Return message to confirm
        return_vals = [success, message]
        return return_vals

    def printReceipt(self, donation_key):
        message = "Receipt open for printing"
        success = True

        d = tools.getKey(donation_key).get()

        #Print receipt to donor
        d.review.archive()
        print_url = d.confirmation.print_url(None)

        #Return message to confirm
        return_vals = [success, message, print_url]
        return return_vals

    def archiveDonation(self, donation_key):
        message = "Donation archived"
        success = True

        d = tools.getKey(donation_key).get()
        d.review.archive()

        #Return message to confirm
        return_vals = [success, message]
        return return_vals

#### ---- Data deletion ---- ####
    def deleteDonation(self, donation_key):
        message = "Donation deleted"
        success = True

        tools.getKey(donation_key).delete()

        #Return message to confirm
        return_vals = [success, message]
        return return_vals

    def deleteContact(self, contact_key):
        message = "Donation deleted"
        success = True

        tools.getKey(contact_key).delete()

        #Return message to confirm
        return_vals = [success, message]
        return return_vals

    def deleteTeam(self, team_key):
        message = "Team deleted"
        success = True

        tools.getKey(team_key).delete()

        #Return message to confirm
        return_vals = [success, message]
        return return_vals

    def semi_deleteIndividual(self, individual_key):
        message = "Individual deleted"
        success = True

        user_key = tools.getUserKey(self)
        
        i_key = tools.getKey(individual_key)
        isAdmin = user_key.get().admin

        if isAdmin == True:
            i_key.delete()
        else:
            if user_key == individual_key:
                i_key.delete()
            else:
                #Access denied - non-admin trying to delete someone else
                message = "Failed - Access denied"
                success = False

        #Return message to confirm 
        return_vals = [success, message]
        return return_vals

app = webapp.WSGIApplication([
    ('/rpc', RPCHandler),
    ], debug=True)
app = appengine_config.recording_add_wsgi_middleware(app)