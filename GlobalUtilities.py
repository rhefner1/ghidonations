# coding: utf-8

import logging, email, exceptions, traceback, string, urllib, json, random, time, re
from time import gmtime, strftime
from datetime import *
from decimal import *

#App Engine platform
from google.appengine.api import taskqueue, mail, memcache, urlfetch, images
from google.appengine.ext.webapp import template
from google.appengine.ext import ndb
from google.appengine.datastore import entity_pb
from google.appengine.datastore.datastore_query import Cursor

#Mailchimp API
from mailsnake import MailSnake

#Sessions
from gaesessions import get_current_session

#Application files
import DataModels as models

###### ------ Authentication ------ ######
def checkCredentials(self, email, password):
    try:
        users = models.Individual.gql("WHERE email = :e", e=email)
        target_user = users.fetch(1)[0]

        if target_user.password == password:
            return True, target_user
        else:
            return False, None
    except:
        return False, None

def checkAuthentication(self, admin_required):
    try:
        #If the cookie doesn't exist, send them back to login
        s_key = getSettingsKey(self)
        u_key = getUserKey(self)

        u = u_key.get()

        #If the user tries to enter an admin page with standard credentials,
        #kick them out.
        if admin_required == True and u.admin == False:
            logging.info("Not authorized - kicking out")
            self.redirect("/ajax/notauthorized")

        #Otherwise, good to go
        return u.admin, s_key.get()

    except Exception, e:
        logging.info("Error in checkAuthentication - kicking out to login page")

        self.redirect("/login")
        return None, None

def RPCcheckAuthentication(self, admin_required):
    try:
        self.session = get_current_session()

        #If the cookie doesn't exist, send them back to login
        if not self.session["key"]:
            return False
        else:
            #The cookie does exist, so store the key
            user_key = getUserKey(self)
            user = user_key.get()

            #Get admin privledges associated with this user
            user_privledges = user.admin

            #If the user tries to enter an admin page with standard credentials,
            #kick them out.
            if admin_required == True and user_privledges == False:
                return "semi"
            
            #Otherwise, good to go
            return True
    except:
        return False

def getUsername(self):
    try:
        user_key = getUserKey(self)
        user = user_key.get()

        return user.name
    except:
        self.redirect("/login")

def getUserKey(self):
    self.session = get_current_session()
    user_key = self.session["key"]

    if user_key == None or user_key == "":
        raise

    return getKey(user_key)

def getSettingsKey(self):
        user_key = getUserKey(self)
        user = user_key.get()
        
        return user.settings

###### ------ Managing entity access w/memcache ------ ######

# Helper Protobuf entity picklers by Nick Johnson
# http://blog.notdot.net/2009/9/Efficient-model-memcaching
def serializeEntities(models):
    if models is None:
        return None
    else:
        entities_list = []
        for m in models:
            e_proto = serializeEntity(m)
            entities_list.append(e_proto)

        return entities_list

def serializeEntity(model):
    if model is None:
        return None
    else:
        # Encoding entity to protobuf
        return ndb.model_to_protobuf(model)

def deserializeEntity(data):
    if data is None:
        return None
    else:
        # Getting entity fro protobuf
        return ndb.model_from_protobuf(data)

def getKey(entity_key):
    return ndb.Key(urlsafe=entity_key)

def gqlCount(gql_object):
    try:
        length = len(gql_object)
    except:
        length = gql_object.count()

    return length

def flushMemcache(self):
    return memcache.flush_all()

def gqlCache(memcache_key, get_item):
    cached_query = memcache.get(memcache_key)

    if not cached_query:
        entities = get_item

        serialized = serializeEntities(entities)
        memcache.set(memcache_key, serialized)

    else: 
        entities = []
        for e in cached_query:
            entity = deserializeEntity(e)
            entities.append(entity)

    return entities

def cache(memcache_key, get_item):
    item_json = memcache.get(memcache_key)

    if not item_json:
        item = get_item()
        memcache.set(memcache_key, json.dumps(item))

    else: 
        item = json.loads(item_json)

    return item

def qCache(q):
    return ndb.get_multi(q.fetch(keys_only=True))

###### ------ Data Access ------ ######
def getAccountEmails(self):
    all_settings = models.Settings.query()
    all_emails = {}

    for s in all_settings:
        all_emails[s.email] = str(s.websafe)
    
    return all_emails

def getMailchimpLists(self, mc_apikey):
    ms = MailSnake(mc_apikey)
    response = ms.lists()

    try:
        mc_lists = {}

        for l in response["data"]:
            list_name = l["name"]
            list_id = l["id"]
            mc_lists[list_name] = list_id

        return [True, mc_lists]
    except:
        if response["code"] == 104:
            return [False, "Sorry, you entered an incorrect Mailchimp API Key"]
        else:
            return [False, "Unknown error"]

###### ------ Data Creation ------ ######
def newSettings(self, name, email):
    new_settings = models.Settings()
    new_settings.name = name
    new_settings.email = email

    new_settings.mc_use = False

    new_settings.impressions = []

    new_settings.amount1 = 10
    new_settings.amount2 = 25
    new_settings.amount3 = 75
    new_settings.amount4 = 100
    new_settings.use_custom = True

    logging.info("Settings created.")

    new_settings.put()

    return new_settings.key

###### ------ Utilities ------ ######
def strArrayToKey(self, str_array):
    key_array = []
    for k in str_array:
        key_array.append(getKey(k))

    return key_array

def shortURL(self, long_url):
    url = "https://www.googleapis.com/urlshortener/v1/url"
    headers = {"Content-Type" : "application/json"}

    params = {"longUrl" : long_url, "key" : "AIzaSyB7k0LsUXibTJHkCx_D3MA0HT6tQAtYZAo"}
    post_params = json.dumps(params)

    result = urlfetch.fetch(url=url, headers=headers, method="POST", payload=post_params, deadline=10)
    response = json.loads(result.content)
    return response["id"]

def getFlash(self):
    try:
        self.session = get_current_session()
        message = self.session["flash"]
        self.session["flash"] = ""
        if message == None:
            message = ""
    except:
        message = ""

    return message

def setFlash(self, message):
    self.session = get_current_session()
    self.session["flash"] = message

def queryCursorDB(query, encoded_cursor):
    num_results = 15
    new_cursor = None
    more = None

    if encoded_cursor:
        query_cursor = Cursor.from_websafe_string(encoded_cursor)
        entities, cursor, more = query.fetch_page(num_results, start_cursor=query_cursor)
    else:
        entities, cursor, more = query.fetch_page(num_results)

    if more:
        new_cursor = cursor.to_websafe_string()
    else:
        new_cursor = None

    return [entities, new_cursor]

def GQLtoDict(self, gql_query):
#Converts GQLQuery of App Engine data models to dictionary objects
    #An empty list to start out with - will be what we return
    all_objects = []

    for o in gql_query:
        new_dict = o.to_dict()
        new_dict["key"] = o.key.urlsafe()
        all_objects.append(new_dict)

    return all_objects

def giveError(self, error_code):
    checkAuthentication(self, False)

    self.error(error_code)
    self.response.out.write(
                   template.render('pages/error.html', {}))

def currentTime():
    #Outputs current date and time
    return convertTime(datetime.utcnow()).strftime("%b %d, %Y %I:%M:%S %p") 

def convertTime(time):
    utc_zone = UTC()
    to_zone = EST()
    time = time.replace(tzinfo=utc_zone)

    new_time = time.astimezone(to_zone)
    return new_time

def toDecimal(number):
    if number != None:
        #Stripping amount donated from commas, etc
        non_decimal = re.compile(r'[^\d.]+')
        number = non_decimal.sub('', str(number))

        return Decimal(number).quantize(Decimal("1.00"))
    else:
        return Decimal(0).quantize(Decimal("1.00"))

def isEmail(email):
    if email:
        if re.match("^.+\\@(\\[?)[a-zA-Z0-9\\-\\.]+\\.([a-zA-Z]{2,3}|[0-9]{1,3})(\\]?)$", email) != None:
            return True
        else:
            return False
    else:
        return False

def mergeContacts(c1_key, c2_key):
    c1 = c1_key.get()
    c2 = c2_key.get()

    #if contact 2 doesn't have an value and contact 1 does,
    #replace c2's value with c1's

    if c2.email == "" and c1.email != "":
        c2.email = c1.email

    if c2.phone == "" and c1.phone != "":
        c2.phone = c1.phone

    if c2.notes == "" or c2.notes == "None" and c1.notes != "":
        c2.notes = c1.notes

    if c2.address == ['', '', '', ''] and c1.address != ['', '', '', '']:
        c2.address = c1.address

    #Merge the donations from c1 all to c2
    for d in c1.data.all_donations:
        d.contact = c2_key
        d.put()

    #Save c2
    c2.put()

    #Finally, delete c1
    c1.key.delete()

###### ------ Utilities Classes ------ ######
class UtilitiesBase():
    def __init__(self, base_entity):
        #Property self.e is an alias back to the original entity
        self.e = base_entity

## -- Settings Classes -- ##
class SettingsData(UtilitiesBase):
    def donations(self, query_cursor):
        query = self.all_donations
        return queryCursorDB(query, query_cursor)

    @property
    def all_donations(self):
        q = models.Donation.gql("WHERE settings = :s ORDER BY donation_date DESC", s=self.e.key)
        return q

    def open_donations(self, query_cursor):
        query = models.Donation.gql("WHERE reviewed = :c AND settings = :s ORDER BY donation_date DESC", c=False, s=self.e.key)
        return queryCursorDB(query, query_cursor)

    @property
    def num_open_donations(self):
        memcache_key = "numopen" + self.e.websafe

        def get_item():
            query = models.Donation.gql("WHERE reviewed = :c AND settings = :s ORDER BY donation_date DESC", c=False, s=self.e.key)
            return gqlCount(query)

        return cache(memcache_key, get_item)

    @property
    def recurring_donors(self):
        donors = []
        for d in self.all_donations:
            if d.isRecurring == True:
                donors.append(d.contact.get())

        return donors
        
    def team_donors(self, team_key):
        donors = []
        donations = models.Donation.gql("WHERE team = :t", t=team_key)
        for d in donations:
            #if d.name not in donors:
            donors.append(d.contact.get())
            
        return donors

    @property
    def undeposited_donations(self):
        q = models.Donation.gql("WHERE settings = :s AND deposited = :d ORDER BY donation_date DESC", s=self.e.key, d=False)
        return qCache(q)

    def deposits(self, query_cursor):
        query = self.all_deposits
        return queryCursorDB(query, query_cursor)

    @property
    def all_deposits(self):
        q = models.DepositReceipt.gql("WHERE settings = :s ORDER BY creation_date DESC", s=self.e.key)
        return q

    def contacts(self, query_cursor):
        query = self.all_contacts
        return queryCursorDB(query, query_cursor)

    @property
    def all_contacts(self):
        q = models.Contact.gql("WHERE settings = :s ORDER BY name", s=self.e.key)
        return q

    def teams(self, query_cursor):
        query = self.all_teams
        return queryCursorDB(query, query_cursor)

    @property
    def all_teams(self):
        q = models.Team.gql("WHERE settings = :k ORDER BY name", k=self.e.key)
        return q

    @property
    def all_individuals(self):
        q = models.Individual.gql("WHERE settings = :k ORDER BY name ASC", k=self.e.key)
        return q

    def individuals(self, query_cursor):
        query = self.all_individuals
        return queryCursorDB(query, query_cursor)

    @property
    def display_teams(self):
        q = models.Team.gql("WHERE settings = :k AND show_team = True ORDER BY name", k=self.e.key)
        return q

    @property
    def teams_dict(self):
        memcache_key = "teamsdict" + self.e.websafe

        def get_item():
            teams = models.Team.gql("WHERE settings = :k AND show_team = :s", k=self.e.key, s=True)

            teams_dict = {}
            for t in teams:
                teams_dict[t.name] = t.websafe

            return teams_dict

        return cache(memcache_key, get_item)

    @property
    def teams_list(self):
        teams = []
        for t in self.teams:
            teams.append(t)
        return teams

    def recurring_info(self, payment_id):
        info = models.RecurringDonationInfo.gql("WHERE payment_id = :id", id=payment_id).fetch(1)[0]
        return info

    ## -- Contact autocomplete -- ##
    @property
    def contactsJSON(self):
        memcache_key = "contacts" + self.e.websafe

        def get_item():
            contacts = []

            for c in self.e.data.all_contacts:
                contact = {}
                contact["label"] = c.name
                contact["email"] = c.email
                contact["address"] = json.dumps(c.address)
                contact["key"] = str(c.websafe)
                
                contacts.append(contact)

            return contacts

        return cache(memcache_key, get_item)

    ## -- Analytics -- ##
    @property
    def one_week_history(self):
        memcache_key = "owh" + self.e.websafe

        def get_item():
            last_week = datetime.today() - timedelta(days=7)

            #Get donations made in the last week
            donations = models.Donation.gql("WHERE settings = :s AND donation_date > :last_week ORDER BY donation_date DESC", 
                        s=self.e.key, last_week=last_week)

            donation_count = 0
            total_money = toDecimal(0)

            for d in donations:
                #Counting total money
                total_money += d.amount_donated
                
                #Counting number of donations
                donation_count += 1

            return [donation_count, str(total_money)]

        return cache(memcache_key, get_item)

class SettingsExists(UtilitiesBase):
    ## -- Check existences -- ##
    def individual(self, email):
        #Check if a user exists in the database - when creating new users
        try:
            user = models.Individual.gql("WHERE settings = :s AND email = :e", s=self.e.key, e=email)

            if user[0]:
                return [True, user[0]]
            else:
                return [False, None]

        except:
            return [False, None]

    def contact(self, name):
        #Check if a user exists in the database - when creating new users
        try:
            #Try checking by name 
            user = models.Contact.gql("WHERE settings = :s AND name = :n", s=self.e.key, n=name)

            if user.fetch(1)[0]:
                return [True, user[0]]
            else:
                return [False, None]

        except:
            return [False, None]

    def entity(self, key):
        exists = True
        try:
            key.get()
        except:
            exists = False

        return exists
    
class SettingsCreate(UtilitiesBase):
    def team(self, name):
        new_team = models.Team()
        new_team.name = name
        new_team.settings = self.e.key
        new_team.show_team = True

        logging.info("Team created.")

        new_team.put()

        return new_team.key

    def individual(self, name, team_key, email, password, admin):
        new_individual = models.Individual()

        new_individual.name = name
        new_individual.email = email
        new_individual.settings = self.e.key
        new_individual.password = password
        new_individual.admin = bool(admin)
        new_individual.description = "[description]"

        new_individual.put()

        new_tl = models.TeamList()
        new_tl.individual = new_individual.key
        new_tl.team = team_key
        new_tl.fundraise_amt = toDecimal("20")
        new_tl.sort_name = name

        new_tl.put()

        memcache.delete("teammembersdict" + team_key.urlsafe())

        logging.info("Individual created.")
        return new_individual.key

    def contact(self, name, email, phone, address, notes, add_mc):
        logging.info("Creating contact for: " + name)
        if name:
            new_contact = models.Contact()
            new_contact.name = name
            new_contact.settings = self.e.key

            if address == None or address == "":
                address = ['', '', '', '']
            if notes == None or notes == "None":
                notes = ""
            if email == None or email == "None":
                email = ""
            if phone == None or phone == "None":
                phone = ""

            new_contact.email = email
            new_contact.phone = phone
            new_contact.address = address
            new_contact.notes = notes

            #Log the contact
            logging.info("Contact created.")

            new_contact.put()

            if add_mc == True and email:
                #Add new contact to Mailchimp
                self.e.mailchimp.add(email, False)

            return new_contact.key
        else:
            logging.error("Cannot create contact because there is not a name.")

    def donation(self, name, email, amount_donated, confirmation_amount, address, team_key, individual_key, add_deposit, payment_id, special_notes, payment_type, email_subscr, ipn_data):
        #All variables being passed as either string or integer
        new_donation = models.Donation()
        new_donation.settings = self.e.key
        new_donation.payment_id = payment_id
        new_donation.payment_type = payment_type
        new_donation.special_notes = special_notes
        new_donation.ipn_data = ipn_data

        new_donation.given_name = name
        new_donation.given_email = email

        def write_contact(query):
            c = query.fetch(1)[0]
            new_donation.contact = c.key

            c.update(name, email, None, None, address)

        query = models.Contact.gql("WHERE settings = :s AND email = :e", s=self.e.key, e=email)
        query2 = models.Contact.gql("WHERE settings = :s AND name = :n", s=self.e.key, n=name)

        if gqlCount(query) != 0 and email:
            write_contact(query)

        elif gqlCount(query2) != 0:
            write_contact(query2)

        else:
            #Add new contact
            c_key = self.contact(name, email, None, address, None, email_subscr)
            new_donation.contact = c_key

        if payment_type == "recurring":
            new_donation.isRecurring = True

        new_donation.amount_donated = toDecimal(amount_donated)
        new_donation.confirmation_amount = toDecimal(confirmation_amount)

        if add_deposit == True:
            logging.info("Adding to undeposited donations.")
            new_donation.deposited = False
        else:
            logging.info("Not adding to undeposited donations")
            new_donation.deposited = True

        if team_key == "" or team_key == "none":
            team_key = None
        if individual_key == "" or individual_key == "none":
            individual_key = None

        new_donation.team = team_key
        new_donation.individual = individual_key
            
        new_donation.put()

        if payment_type != "offline":
            #Go ahead and send the confirmation email automatically
            new_donation.confirmation.task(86400)
            new_donation.review.archive()

    def recurring_donation(self, payment_id, duration, ipn_data):
        new_recurring = models.RecurringDonationInfo()
        new_recurring.payment_id = payment_id
        new_recurring.duration = duration
        new_recurring.ipn_data = ipn_data

        new_recurring.put()

    def deposit_receipt(self, entity_keys):
        new_deposit = models.DepositReceipt()

        new_deposit.entity_keys = entity_keys
        new_deposit.settings = self.e.key
        new_deposit.time_deposited = currentTime()

        new_deposit.put()

class SettingsDeposits(UtilitiesBase):
    def deposit(self, unicode_keys):
        #Changing all unicode keys into Key objects
        donation_keys = []
        for key in unicode_keys:
            donation_keys.append(getKey(key))

        for key in donation_keys:
            d = key.get()
            d.deposited = True
            d.put()

        self.e.create.deposit_receipt(donation_keys)

    def remove(self, donation_keys):
        for key in donation_keys:
            d = key.get()
            d.deposited = None
            d.put()

class SettingsMailchimp(UtilitiesBase):
    def add(self, email, task_queue):
        if self.e.mc_use == True:
        #Check if the settings indicate to use Mailchimp

            if isEmail(email):
                ms = MailSnake(self.e.mc_apikey)
                try:               
                    #[ MailChimp API v1.3 documentation ]
                    #http://www.mailchimp.com/api/1.3/
                    
                    #http://apidocs.mailchimp.com/api/1.3/listsubscribe.func.php
                    #listSubscribe(string apikey, string id, string email_address, array merge_vars, string email_type, 
                    #bool double_optin, bool update_existing, bool replace_interests, bool send_welcome)

                    response = ms.listSubscribe(id=self.e.mc_donorlist, email_address=email)

                    logging.info("Mailchimp response: " + str(response))

                    if response == True:
                        logging.info("Email address added to database.")

                    elif response["code"] == 214:
                        logging.info("Already in database. No action required.")
                    
                    else:
                    #Must be an error if not True and not error 214 - raise error
                        raise

                except:
                    if task_queue == False:
                    #This is the original request, so add to task queue.
                        logging.error("An error occured contacting Mailchimp. Added to task queue to try again.")
                        taskqueue.add(url="/tasks/mailchimp", params={'email' : email, 'settings' : self.e.websafe})
                        
                    else:
                    #If this is coming from the task queue, fail it (so the task queue retry mechanism works)
                        self.error(500)
                        logging.info("Request from task queue failed. Sending back 500 error.")

            else:
                logging.info("Not a valid email address. Not continuing.")

## -- Team Classes -- ##
class TeamData(UtilitiesBase):
    @property
    def donation_total(self):
        team_key = self.e.key
        memcache_key = "tdtotal" +  team_key.urlsafe()
        
        def get_item():
            settings = self.e.settings

            q = models.Donation.gql("WHERE settings = :s AND team = :t", s=settings, t=team_key)
            donations = qCache(q)

            donation_total = toDecimal(0)

            for d in donations:
                donation_total += d.amount_donated

            return str(donation_total)

        item = cache(memcache_key, get_item) 
        return toDecimal(item)

    @property
    def donations(self):
        q = models.Donation.gql("WHERE settings = :s AND team = :t ORDER BY donation_date", s=self.e.settings, t=self.e.key)
        return qCache(q)

    @property
    def members(self):
        q = models.TeamList.gql("WHERE team = :t ORDER BY sort_name", t=self.e.key)
        return qCache(q)

    @property
    def members_dict(self):
        memcache_key = "teammembersdict" +  self.e.websafe
        members = self.members
        
        def get_item():
            members_dict = {}
            for tl in members:
                i = tl.individual.get()
                members_dict[i.name] = i.websafe

            return members_dict

        return cache(memcache_key, get_item)

    @property
    def members_list(self):
        memcache_key = "teammembers" +  self.e.websafe
        
        def get_item():
            members = self.members
            all_members = []

            for tl in members:
                tl_key = tl.individual.urlsafe()
                member = []
                member.append(tl.individual_name)
                member.append(tl.individual.get().data.photo_url)        
                member.append(tl_key)

                #Attaching this to the main array
                all_members.append(member)

            return all_members

        return cache(memcache_key, get_item)

## -- Individual Classes -- ##
class IndividualData(UtilitiesBase):
    @property
    def donation_total(self):
        memcache_key = "idtotal" + self.e.websafe

        def get_item():
            settings = self.e.settings
            individual_key = self.e.key

            q = models.Donation.gql("WHERE settings = :s AND individual = :i", s=settings, i=individual_key)
            donations = qCache(q)

            donation_total = toDecimal(0)

            for d in donations:
                donation_total += d.amount_donated

            return str(donation_total)

        item = cache(memcache_key, get_item)
        return toDecimal(item)

    def info(self, team):
        memcache_key = "info" + team.urlsafe() + self.e.websafe
        def get_item():
            if self.e.photo:
                image_url = images.get_serving_url(self.e.photo, 150)
            else:
                image_url = "https://ghidonations.appspot.com/images/face150.jpg"

            tl = self.getTeamList(team)
            percentage = int(float(tl.donation_total / tl.fundraise_amt) * 100)

            if percentage > 100:
                percentage = 100
            elif percentage <0:
                percentage = 0

            message = str(percentage) + "% to goal of $" + str(tl.fundraise_amt)
                
            return [image_url, self.e.name, self.e.description, percentage, message]

        return cache(memcache_key, get_item)

    @property
    def donations(self):
        q = models.Donation.gql("WHERE individual = :i ORDER BY donation_date", i=self.e.key)
        return qCache(q)

    @property
    def teams(self):
        q = models.TeamList.gql("WHERE individual = :i", i=self.e.key)
        return q

    @property
    def team_list(self):
        teams_dict = {}

        for t in self.teams:
            array = [t.team.get().name, str(t.fundraise_amt)]
            teams_dict[t.team.urlsafe()] = array

        return teams_dict

    @property
    def team_json(self):
        return json.dumps(self.team_list)

    @property
    def photo_url(self):
        if self.e.photo != None:
            try:
                photo = images.get_serving_url(self.e.photo, 200, secure_url=True)
            except:
                photo = "/images/face.jpg"
        else:
            photo = "/images/face.jpg"

        return photo

    def getTeamList(self, team):
        query = models.TeamList.gql("WHERE individual = :i AND team = :t", i=self.e.key, t=team)
        return query.fetch(1)[0]

## -- Donation Classes -- ##
class DonationData(UtilitiesBase):
    @property
    def team_name(self):
        if self.e.team != None:
            return self.e.team.get().name
        else:
            return None

    @property
    def individual_name(self):
        if self.e.individual != None:
            return self.e.individual.get().name
        else:
            return None

class DonationReview(UtilitiesBase):
    ## -- Review Queue -- ##
    def archive(self):
        self.e.reviewed = True
        self.e.put()

    def markUnreviewed(self):
        self.e.reviewed = False
        self.e.put()

class DonationAssign(UtilitiesBase):
    ## -- Associating Donations With Team/Individual -- ##
    def associateTeam(self, team_key, writeback):
        if self.e.team != team_key:
        #Just to make sure the association is actually changed - instead of marking the same value as it was before
            try:
                message = "Donation " + self.e.websafe +  " associated with team" + str(team_key.urlsafe()) + "."
                logging.info(message)
            except:
                pass

            self.e.team = team_key

        if writeback == True:
            self.e.put()

    def disassociateTeam(self, writeback):
        if self.e.team != None:
        #Just to make sure the association is actually changed - instead of marking the same value as it was before
            message = "Donation " + self.e.websafe +  " removed from team" + str(self.e.team.urlsafe()) + "."
            logging.info(message)

            self.e.team = None

        if writeback == True:
            self.e.put()

    def associateIndividual(self, individual_key, writeback):
        if self.e.individual != individual_key:
        #Just to make sure the association is actually changed - instead of marking the same value as it was before
            try:
                message = "Donation " + self.e.websafe +  " associated with individual" + str(individual_key.urlsafe()) + "."
                logging.info(message)
            except:
                pass

            self.e.individual = individual_key

        if writeback == True:
            self.e.put()

    def disassociateIndividual(self, writeback):
        if self.e.individual != None:
        #Just to make sure the association is actually changed - instead of marking the same value as it was before
            message = "Donation " + self.e.websafe +  " removed from individual" + str(self.e.individual.urlsafe()) + "."
            logging.info(message)

            self.e.individual = None

        if writeback == True:
            self.e.put()

class DonationConfirmation(UtilitiesBase):
    ## -- Confirmation Letter -- ##
    def print_url(self, who):
        if not who:
            who = ""

        return who + "/thanks?m=p&id=" + self.e.websafe

    def see_url(self, who):
        if not who:
            who = ""

        return who + "/thanks?m=w&id=" + self.e.websafe

    def task(self, countdown_secs):
        logging.info("Tasking confirmation email.  Delaying for " + str(countdown_secs) + " seconds.")
        taskqueue.add(url="/tasks/confirmation", params={'donation_key' : self.e.websafe}, countdown=int(countdown_secs))

    def email(self):
        d = self.e

        message = mail.EmailMessage()
        message.to = d.email

        ## TODO - is there any other way to get an organization's email address to appear if it's not verified?
        settings_name = d.settings.get().name
        if settings_name == "GHI":
            message.sender = "donate@globalhopeindia.org"
            message.subject = "Thanks for your donation!"
        else:
            message.sender = "mailer@ghidonations.appspotmail.com"
            message.subject = settings_name + " - Thanks for your donation!"

        date = convertTime(d.donation_date).strftime("%B %d, %Y")
        s = d.settings.get()

        if d.individual:
            individual_name = d.individual.get().name
        elif d.team:
            individual_name = d.team.get().name
        else:
            individual_name = None

        template_variables = {"s": s, "d" : d, "date" : date, "individual_name" : individual_name}

        who = "http://ghidonations.appspot.com"

        template_variables["see_url"] = d.confirmation.see_url(who)
        template_variables["print_url"] = d.confirmation.print_url(who)
 
        #Message body/HTML here
        message.html = template.render("pages/letters/thanks_email.html", template_variables)

        logging.info("Sending confirmation email to: " + d.email)

        #Adding to history
        logging.info("Confirmation email sent at " + currentTime())

        message.send()

## -- Contact Classes -- ##
class ContactData(UtilitiesBase):
    def donations(self, query_cursor):
        query = self.all_donations
        return queryCursorDB(query, query_cursor)

    @property
    def all_donations(self):
        q = models.Donation.gql("WHERE settings = :s AND contact = :c ORDER BY donation_date DESC", s=self.e.settings, c=self.e.key)
        return q

    def impressions(self, query_cursor):
        query = self.all_impressions
        return queryCursorDB(query, query_cursor)

    @property 
    def all_impressions(self):
        q = models.Impression.gql("WHERE contact = :c ORDER BY creation_date DESC", c=self.e.key)
        return q

class ContactCreate(UtilitiesBase):
    def impression(self, impression, notes):
        new_impression = models.Impression()

        new_impression.contact = self.e.key
        new_impression.impression = impression
        new_impression.notes = notes

        new_impression.put()

## -- Dictionary Difference Class -- ##
class DictDiffer(object):
    """
    Calculate the difference between two dictionaries as:
    (1) items added
    (2) items removed
    (3) keys same in both but changed values
    (4) keys same in both and unchanged values
    """
    def __init__(self, current_dict, past_dict):
        self.current_dict, self.past_dict = current_dict, past_dict
        self.set_current, self.set_past = set(current_dict.keys()), set(past_dict.keys())
        self.intersect = self.set_current.intersection(self.set_past)
    def added(self):
        return self.set_current - self.intersect
    def removed(self):
        return self.set_past - self.intersect
    def changed(self):
        return set(o for o in self.intersect if self.past_dict[o] != self.current_dict[o])
    def unchanged(self):
        return set(o for o in self.intersect if self.past_dict[o] == self.current_dict[o])
    
###### ------ Time classes ------ ######

class EST(tzinfo): 
    def utcoffset(self,dt): 
        return timedelta(hours=-4,minutes=0) 
    def tzname(self,dt): 
        return "GMT -4" 
    def dst(self,dt): 
        return timedelta(0) 

class UTC(tzinfo):
    def utcoffset(self, dt):
        return timedelta(0)
    def tzname(self, dt):
        return "UTC"
    def dst(self, dt):
        return timedelta(0)