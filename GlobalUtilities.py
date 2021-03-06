# coding: utf-8

import appengine_config
import datetime
import json
import logging
import os
import pipeline
import re
import time
from decimal import *

# App Engine platform
from google.appengine.api import taskqueue, mail, memcache, images
from google.appengine.ext.webapp import template
from google.appengine.ext import ndb, deferred

import endpoints
from google.appengine.datastore.datastore_query import Cursor

# Google Cloud Storage
import cloudstorage as gcs

# Mailchimp API
from mailsnake import MailSnake

# Sessions
from gaesessions import get_current_session

# Application files
import DataModels as models

# Search
from google.appengine.api import search

_CONTACT_SEARCH_INDEX = "contact"
_DEPOSIT_SEARCH_INDEX = "deposit"
_DONATION_SEARCH_INDEX = "donation"
_INDIVIDUAL_SEARCH_INDEX = "individual"
_TEAM_SEARCH_INDEX = "team"
_NUM_RESULTS = 15


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


def checkAuthentication(self, admin_required, from_endpoints=False):
    try:
        # If the cookie doesn't exist, send them back to login
        u_key = getUserKey(self)
        u = u_key.get()

        # If the user tries to enter an admin page with standard credentials,
        # kick them out.
        if admin_required == True and u.admin == False:
            logging.info("Not authorized - kicking out")
            self.redirect("/ajax/notauthorized")

        # Otherwise, good to go
        return u.admin, u.settings.get()

    except Exception as e:
        message = "Error in checkAuthentication - kicking out to login page. " + str(e)
        logging.info(message)

        if from_endpoints:
            raise endpoints.ForbiddenException(message)
        else:
            self.redirect("/login")

        return None, None


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
        raise Exception("User key is none")

    return getKey(user_key)


def getSettingsKey(self, endpoints=False):
    try:
        user_key = getUserKey(self)
        user = user_key.get()

        return user.settings

    except Exception as e:
        if endpoints:
            raise Exception("Error in getSettingsKey")
        else:
            self.redirect("/login")


def RPCcheckAuthentication(self, admin_required):
    try:
        self.session = get_current_session()

        # If the cookie doesn't exist, send them back to login
        if not self.session["key"]:
            return False
        else:
            # The cookie does exist, so store the key
            user_key = getUserKey(self)
            user = user_key.get()

            # Get admin privledges associated with this user
            user_privledges = user.admin

            # If the user tries to enter an admin page with standard credentials,
            # kick them out.
            if admin_required == True and user_privledges == False:
                return "semi"

            # Otherwise, good to go
            return True
    except:
        return False


###### ------ Managing entity access w/memcache ------ ######

# Helper Protobuf entity picklers by Nick Johnson
# http://blog.notdot.net/2009/9/Efficient-model-memcaching
def cache(memcache_key, get_item):
    item_json = memcache.get(memcache_key)

    if not item_json:
        item = get_item()
        memcache.set(memcache_key, json.dumps(item))

    else:
        item = json.loads(item_json)

    return item


def deserializeEntity(data):
    if data is None:
        return None
    else:
        # Getting entity fro protobuf
        return ndb.model_from_protobuf(data)


def flushMemcache():
    return memcache.flush_all()


def getKey(entity_key):
    return ndb.Key(urlsafe=entity_key)


def getKeyIfExists(websafe_key):
    try:
        key = getKey(websafe_key)
        obj = key.get()

        # If exception hasn't been thrown, the key exists
        return key
    except:
        return None


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


def gqlCount(gql_object):
    try:
        length = len(gql_object)
    except:
        length = gql_object.count()

    return length


def qCache(q):
    return ndb.get_multi(q.fetch(keys_only=True))


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


###### ------ Data Access ------ ######
def getAccountEmails():
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
            mc_lists[list_name] = l["id"]

        return [True, mc_lists]
    except:
        if response["code"] == 104:
            return [False, "Sorry, you entered an incorrect Mailchimp API Key"]
        else:
            return [False, "Unknown error"]


###### ------ Data Creation ------ ######
def newSettings(name, email):
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


###### ------ Spreadsheet Export Controller Utilities ------ ######
def checkTaskCompletion(s, job_id):
    m = memcache.get(job_id)
    if m == None or m == 0:
        return False, None
    else:
        return True, m


def getAllSearchDocs(index_name):
    index = search.Index(name=index_name)

    documents = []
    last_doc_id = None
    completed = False

    while (completed == False):
        docs_query = index.get_range(start_id=last_doc_id, limit=1000, include_start_object=False)

        if docs_query.results != []:
            documents.extend(docs_query.results)
            last_doc_id = docs_query.results[-1].doc_id

        else:
            completed = True

    return documents


def newFile(mime_type, file_name):
    gcs_file_key = appengine_config.GCS_BUCKET + "/" + file_name

    write_retry_params = gcs.RetryParams(backoff_factor=1.1)
    gcs_file = gcs.open(gcs_file_key, 'w', content_type=mime_type,
                        retry_params=write_retry_params)

    return gcs_file_key, gcs_file


###### ------ Deferred Utilities ------ ######
def indexEntitiesFromQuery(query, query_cursor=None):
    entities, new_cursor, more = query.fetch_page(20, start_cursor=query_cursor, keys_only=True)

    # If there are more results, kick off concurrent request to get things done faster
    if new_cursor != None:
        deferred.defer(indexEntitiesFromQuery, query, query_cursor=new_cursor, _queue="backend")

    for e in entities:
        taskqueue.add(url="/tasks/delayindexing", params={'e': e.urlsafe()}, queue_name="delayindexing")


###### ------ Utilities ------ ######
def currentTime():
    # Outputs current date and time
    return convertTime(datetime.datetime.utcnow()).strftime("%b %d, %Y %I:%M:%S %p")


def convertTime(time):
    utc_zone = UTC()
    to_zone = EST()
    time = time.replace(tzinfo=utc_zone)

    new_time = time.astimezone(to_zone)
    return new_time


def getWebsafeCursor(cursor_object):
    if cursor_object:
        return cursor_object.web_safe_string
    else:
        return None


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


def getGlobalSettings():
    q = models.GlobalSettings.query()

    try:
        global_settings = q.fetch(1)[0]

    except:
        new_global_settings = models.GlobalSettings()
        new_global_settings.cookie_key = os.urandom(64).encode("base64")
        global_settings = new_global_settings.put()

        global_settings = global_settings.get()

    return global_settings


def getSearchDoc(doc_id, index):
    if not doc_id:
        return None

    try:
        response = index.get_range(
            start_id=doc_id, limit=1, include_start_object=True)

        if response.results and response.results[0].doc_id == doc_id:
            return response.results[0]

        return None

    except search.InvalidRequest:  # catches ill-formed doc ids
        return None


def giveError(self, error_code):
    # checkAuthentication(self, False)

    self.error(error_code)
    self.response.write(
        template.render('pages/error.html', {}))


def GQLtoDict(self, gql_query):
    # Converts GQLQuery of App Engine data models to dictionary objects
    # An empty list to start out with - will be what we return
    all_objects = []

    for o in gql_query:
        new_dict = o.to_dict()
        new_dict["key"] = o.key.urlsafe()
        all_objects.append(new_dict)

    return all_objects


def isEmail(email):
    if email:
        if re.match("^.+\\@(\\[?)[a-zA-Z0-9\\-\\.]+\\.([a-zA-Z]{2,3}|[0-9]{1,3})(\\]?)$", email) != None:
            return True
        else:
            return False
    else:
        return False


def listDiff(list1, list2):
    # Typically old value is list1, new value is list2
    list_diff = list(set(list2) - set(list1))

    try:
        list_diff.remove('')
    except:
        pass

    return list_diff


def mergeContacts(c1_key, c2_key):
    c1 = c1_key.get()
    c2 = c2_key.get()

    # Ff contact 2 doesn't have an value and contact 1 does,
    # replace c2's value with c1's

    combined_emails = c2.email + c1.email

    try:
        combined_emails.remove("")
    except:
        pass

    c2.email = combined_emails

    if c2.phone == "" and c1.phone != "":
        c2.phone = c1.phone

    if c2.notes == "" or c2.notes == "None" and c1.notes != "":
        c2.notes = c1.notes

    if c2.address == ['', '', '', ''] and c1.address != ['', '', '', '']:
        c2.address = c1.address

    # Merge the donations from c1 all to c2
    for d in c1.data.all_donations:
        d.contact = c2_key
        d.put()

    # Save c2
    c2.put()

    # Finally, delete c1
    c1.key.delete()


def moneyAmount(money_string):
    money = toDecimal(money_string)
    money = "${:,.2f}".format(money)
    return money


def ndbKeyToUrlsafe(keys):
    urlsafe_keys = []

    for k in keys:
        urlsafe_keys.append(k.urlsafe())

    return urlsafe_keys


def pipelineStatus(job_id):
    pipeline_id = memcache.get("id" + job_id)

    if pipeline_id:
        status_tree = pipeline.get_status_tree(pipeline_id)

        total_pipelines = 0
        pipelines_finished = 0

        for pipe in status_tree["pipelines"].values():

            status = pipe['status']
            logging.info(status)

            if status == "aborted":
                logging.error("Error in pipelineStatus with job_id: " + job_id)

            if status == "filled" or status == "done":
                pipelines_finished += 1

            total_pipelines += 1

        percentage = float(pipelines_finished) / float(total_pipelines)
        return int(percentage * 100)

    else:
        logging.debug("Could not find pipeline_id, defaulting to status=0")
        return 0


def queryCursorDB(query, encoded_cursor, keys_only=False, num_results=_NUM_RESULTS):
    new_cursor = None
    more = None

    if encoded_cursor:
        query_cursor = Cursor.from_websafe_string(encoded_cursor)
        entities, cursor, more = query.fetch_page(num_results, start_cursor=query_cursor, keys_only=keys_only)
    else:
        entities, cursor, more = query.fetch_page(num_results, keys_only=keys_only)

    if more:
        new_cursor = cursor.to_websafe_string()
    else:
        new_cursor = None

    return [entities, new_cursor]


def searchReturnAll(query, search_results, settings, search_function, entity_return=True):
    all_results = []
    results = search_results

    end_of_results = False

    while (end_of_results == False):
        if entity_return == True:
            all_results += searchToEntities(results)

        else:
            all_results.extend(searchToDocuments(results))

        query_cursor = results.cursor
        if query_cursor == None:
            # Stop the loop
            end_of_results = True

        else:
            # Otherwise, fetch the next results
            results = search_function(query, query_cursor=query_cursor, entity_return=entity_return)[0]

    return all_results


def searchToDocuments(search_results):
    documents = []

    for r in search_results:
        documents.append(r)

    return documents


def searchToEntities(search_results):
    entities = []

    for r in search_results:
        key = r.fields[0].value
        d = getKey(key).get()
        entities.append(d)

    return entities


def setFlash(self, message):
    self.session = get_current_session()
    self.session["flash"] = message


def strArrayToKey(self, str_array):
    key_array = []
    for k in str_array:
        key_array.append(getKey(k))

    return key_array


def toDecimal(number):
    if number != None:
        # Stripping amount donated from commas, etc
        non_decimal = re.compile(r'[^\d.-]+')
        number = non_decimal.sub('', str(number))

        return Decimal(number).quantize(Decimal("1.00"))
    else:
        return Decimal(0).quantize(Decimal("1.00"))


def truncateEmail(email, is_list=False):
    if is_list == True:
        new_email = ""
        for e in email:
            new_email += e + " "

        email = new_email

    truncation_length = 35
    if len(email) > truncation_length:
        email = email[0:truncation_length]
        email = email.replace(' ', ', ')
        email += "..."

    return email


def writeEntities(e_key):
    e = e_key.get()
    if isinstance(e.email, basestring):
        email = e.email
        e.email = [email]
        e.put()


###### ------ Utilities Classes ------ ######
class UtilitiesBase():
    def __init__(self, base_entity):
        # Property self.e is an alias back to the original entity
        self.e = base_entity


## -- Settings Classes -- ##
class SettingsCreate(UtilitiesBase):
    def contact(self, name, email=None, phone=None, address=None, notes=None, add_mc=False):
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
                email = [""]
            if isinstance(email, basestring):
                email = [email]
            if phone == None or phone == "None":
                phone = ""

            new_contact.email = email
            new_contact.phone = phone
            new_contact.address = address
            new_contact.notes = notes

            # Log the contact
            logging.info("Contact created.")

            new_contact.put()

            if add_mc == True:
                for e in email:
                    if e and e != "":
                        # Add new contact to Mailchimp
                        self.e.mailchimp.add(e, name, False)

            return new_contact.key
        else:
            logging.error("Cannot create contact because there is not a name.")

    def deposit_receipt(self, entity_keys):
        new_deposit = models.DepositReceipt()

        new_deposit.entity_keys = entity_keys
        new_deposit.settings = self.e.key
        new_deposit.time_deposited = currentTime()

        new_deposit.put()

    def donation(self, name, email, amount_donated, payment_type, confirmation_amount=None, phone=None, address=None,
                 team_key=None, individual_key=None, add_deposit=True, payment_id=None, special_notes=None,
                 email_subscr=False, ipn_data=None, contact_key=None):
        if confirmation_amount == None:
            confirmation_amount = amount_donated

        # All variables being passed as either string or integer
        new_donation = models.Donation()
        new_donation.settings = self.e.key
        new_donation.payment_id = payment_id
        new_donation.payment_type = payment_type
        new_donation.special_notes = special_notes
        new_donation.ipn_data = ipn_data

        new_donation.given_name = name
        new_donation.given_email = email

        if not contact_key:
            exists = self.e.exists.contact(email=email, name=name)
            if exists[0]:
                c = exists[1]
                contact_key = c.key
            else:
                # Add new contact
                contact_key = self.contact(name, email=email, phone=phone, address=address, add_mc=email_subscr)

        new_donation.contact = contact_key

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

        # If designated, re-index team and individual
        if team_key:
            taskqueue.add(url="/tasks/delayindexing", params={'e': team_key.urlsafe()}, countdown=5,
                          queue_name="delayindexing")

        if individual_key:
            taskqueue.add(url="/tasks/delayindexing", params={'e': individual_key.urlsafe()}, countdown=5,
                          queue_name="delayindexing")

        if payment_type != "offline":

            if special_notes != "" and special_notes != None:
                email = mail.EmailMessage()
                email.sender = "GHI Donations <mailer@ghidonations.appspotmail.com>"
                email.subject = "New Donation with Note"
                email.to = self.e.email

                message = """
A new note was received from {name} for ${confirmation_amount} ({payment_type} donation): <br>

<strong>{special_notes}</strong> <br><br>

You can view this donation at <a href="https://ghidonations.appspot.com/#contact?c={contact_key}">https://ghidonations.appspot.com/contact?c={contact_key}</a>.<br><br>
Thanks!"""

                message = message.format(payment_type=payment_type, name=name, confirmation_amount=confirmation_amount,
                                         special_notes=special_notes.encode('utf-8', 'ignore'),
                                         contact_key=new_donation.contact.urlsafe())

                email.html = message
                email.send()

            # Go ahead and send the confirmation email automatically
            new_donation.confirmation.task(86400)
            new_donation.review.archive()

        return new_donation.key

    def individual(self, name, team_key, email, password, admin=False):
        new_individual = models.Individual()

        new_individual.name = name
        new_individual.settings = self.e.key
        new_individual.admin = bool(admin)
        new_individual.description = "Thank you for supporting my short-term mission trip to India. Your prayer and financial support is greatly needed and appreciated. Thanks for helping make it possible for me to go join God in His work in India."

        if email:
            new_individual.email = email
            new_individual.password = password

        new_individual.put()

        new_tl = models.TeamList()
        new_tl.individual = new_individual.key
        new_tl.team = team_key
        new_tl.fundraise_amt = toDecimal("2900")
        new_tl.sort_name = name

        new_tl.put()

        memcache.delete("teammembersdict" + team_key.urlsafe())

        logging.info("Individual created.")
        return new_individual.key

    def recurring_donation(self, payment_id, duration, ipn_data=None):
        new_recurring = models.show_donation_page()
        new_recurring.payment_id = payment_id
        new_recurring.duration = duration
        new_recurring.ipn_data = ipn_data

        new_recurring.put()

    def team(self, name):
        new_team = models.Team()
        new_team.name = name
        new_team.settings = self.e.key
        new_team.show_team = True

        logging.info("Team created.")

        new_team.put()

        return new_team.key

        return new_donation.key.urlsafe()


class SettingsData(UtilitiesBase):
    @property
    def all_contacts(self):
        q = models.Contact.gql("WHERE settings = :s ORDER BY name", s=self.e.key)
        return q

    @property
    def all_deposits(self):
        q = models.DepositReceipt.gql("WHERE settings = :s ORDER BY creation_date DESC", s=self.e.key)
        return q

    @property
    def all_donations(self):
        q = models.Donation.gql("WHERE settings = :s ORDER BY donation_date DESC", s=self.e.key)
        return q

    @property
    def all_individuals(self):
        q = models.Individual.gql("WHERE settings = :k ORDER BY name ASC", k=self.e.key)
        return q

    @property
    def all_teams(self):
        q = models.Team.gql("WHERE settings = :k ORDER BY name", k=self.e.key)
        return q

    def contacts(self, query_cursor):
        query = self.all_contacts
        return queryCursorDB(query, query_cursor)

    def deposits(self, query_cursor):
        query = self.all_deposits
        return queryCursorDB(query, query_cursor)

    @property
    def display_teams(self):
        q = models.Team.gql("WHERE settings = :k AND show_team = True ORDER BY name", k=self.e.key)
        return q

    def donations(self, query_cursor):
        query = self.all_donations
        return queryCursorDB(query, query_cursor)

    def individuals(self, query_cursor):
        query = self.all_individuals
        return queryCursorDB(query, query_cursor)

    @property
    def num_open_donations(self):
        memcache_key = "numopen" + self.e.websafe

        def get_item():
            query = models.Donation.gql("WHERE reviewed = :c AND settings = :s ORDER BY donation_date DESC", c=False,
                                        s=self.e.key)
            return gqlCount(query)

        return cache(memcache_key, get_item)

    def open_donations(self, query_cursor):
        query = models.Donation.gql("WHERE reviewed = :c AND settings = :s ORDER BY donation_date DESC", c=False,
                                    s=self.e.key)
        return queryCursorDB(query, query_cursor)

    @property
    def recurring_donors(self):
        donors_dict = {}
        query = models.Donation.gql("WHERE settings = :s AND isRecurring = :r", s=self.e.key, r=True)

        for d in query:
            # Adding to dictionary first to manage duplicates
            websafe = d.contact

            if not websafe in donors_dict:
                donors_dict[websafe] = d.contact.get()

        donors = []
        for k in donors_dict:
            # Now creating a normal iterable array of just entities
            donors.append(donors_dict[k])

        return donors

    def recurring_info(self, payment_id):
        info = models.show_donation_page.gql("WHERE payment_id = :id", id=payment_id).fetch(1)[0]
        return info

    def team_donors(self, team_key):
        donors = []
        donations = models.Donation.gql("WHERE team = :t", t=team_key)
        for d in donations:
            # if d.name not in donors:
            donors.append(d.contact.get())

        return donors

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

    def teams(self, query_cursor):
        query = self.all_teams
        return queryCursorDB(query, query_cursor)

    @property
    def undeposited_donations(self):
        q = models.Donation.gql("WHERE settings = :s AND deposited = :d ORDER BY donation_date DESC", s=self.e.key,
                                d=False)
        return qCache(q)

    ## -- Analytics -- ##
    @property
    def one_week_history(self):
        return json.loads(self.e.one_week_history)

    @property
    def one_month_history(self):
        return json.loads(self.e.one_month_history)

    ## -- Contact autocomplete -- ##
    @property
    def contactsJSON(self):
        memcache_key = "contacts" + self.e.websafe

        def get_item():
            return self.e.contacts_json

        return cache(memcache_key, get_item)


class SettingsDeposits(UtilitiesBase):
    def deposit(self, unicode_keys):
        # Changing all unicode keys into Key objects
        donation_keys = []
        for key in unicode_keys:
            donation_keys.append(getKey(key))

        self.e.create.deposit_receipt(donation_keys)

        for key in donation_keys:
            d = key.get()
            d.deposited = True
            d.put()

    def remove(self, unicode_keys):
        # Changing all unicode keys into Key objects
        donation_keys = []
        for key in unicode_keys:
            donation_keys.append(getKey(key))

        for key in donation_keys:
            d = key.get()
            d.deposited = None
            d.put()


class SettingsExists(UtilitiesBase):
    ## -- Check existences -- ##
    def _check_contact_email(self, email):
        try:
            if email == None or email == "":
                return [False, None]
            else:
                query = models.Contact.query(models.Contact.settings == self.e.key,
                                             models.Contact.email == email)

                if gqlCount(query) != 0:
                    return [True, query.fetch(1)[0]]
                else:
                    return [False, None]

        except:
            return [False, None]

    def _check_contact_name(self, name):
        try:
            query = models.Contact.query(models.Contact.settings == self.e.key,
                                         models.Contact.name == name)

            if gqlCount(query) != 0:
                return [True, query.fetch(1)[0]]
            else:
                return [False, None]

        except:
            return [False, None]

    def contact(self, email=None, name=None):
        # Email can be either a str or a list. Name must be str

        if not email and not name:
            raise Exception("Must have either a name or email to determine if contact exists.")

        # Default doesn't exist response
        exists = [False, None]

        if isinstance(email, set):
            email = list(email)

        # Check by email first
        if email:
            if isinstance(email, basestring):
                exists = self._check_contact_email(email)

            elif isinstance(email, list):
                for e in email:
                    # Check if the contact exists by email
                    email_exists = self._check_contact_email(e)

                    if email_exists[0]:
                        exists[0] = True

                        # Add matched contact
                        if isinstance(exists[1], list):
                            exists[1].append(email_exists[1])
                        else:
                            exists[1] = [email_exists[1]]

            else:
                logging.error("Email is of type: " + str(type(email)))
                raise Exception("Wrong variable type for email.")

        # If name provided and the first test fails, try matching by name
        if name and exists[0] == False:
            exists = self._check_contact_name(name)

        # If matched contact list only contains one item, take it out of list
        if isinstance(exists[1], list) and len(exists[1]) == 1:
            exists[1] = exists[1][0]

        return exists

    def entity(self, key):
        exists = True
        try:
            key.get()
        except:
            exists = False

        return exists

    def individual(self, email):
        # Check if a user exists in the database - when creating new users
        try:
            user = models.Individual.gql("WHERE settings = :s AND email = :e", s=self.e.key, e=email)

            user_entity = user.fetch(1)[0]
            if user_entity:
                return [True, user_entity]
            else:
                return [False, None]

        except:
            return [False, None]


class SettingsMailchimp(UtilitiesBase):
    def add(self, email, name, task_queue):
        if self.e.mc_use == True:
            # Check if the settings indicate to use Mailchimp

            if isEmail(email):
                ms = MailSnake(self.e.mc_apikey)
                try:
                    # [ MailChimp API v1.3 documentation ]
                    # http://www.mailchimp.com/api/1.3/

                    # http://apidocs.mailchimp.com/api/1.3/listsubscribe.func.php
                    # listSubscribe(string apikey, string id, string email_address, array merge_vars, string email_type,
                    # bool double_optin, bool update_existing, bool replace_interests, bool send_welcome)
                    name_split = name.split()
                    merge_vars = {"FNAME": name_split[0], "LNAME": " ".join(name_split[1:])}

                    response = ms.listSubscribe(id=self.e.mc_donorlist, email_address=email, merge_vars=merge_vars)

                    logging.info("Mailchimp response: " + str(response))

                    if response == True:
                        logging.info("Email address added to database.")

                    elif response["code"] == 214:
                        logging.info("Already in database. No action required.")

                    else:
                        # Must be an error if not True and not error 214 - raise error
                        raise

                except:
                    if task_queue == False:
                        # This is the original request, so add to task queue.
                        logging.error("An error occured contacting Mailchimp. Added to task queue to try again.")
                        taskqueue.add(url="/tasks/mailchimp",
                                      params={'email': email, 'name': name, 'settings': self.e.websafe},
                                      queue_name="mailchimp")

                    else:
                        # If this is coming from the task queue, fail it (so the task queue retry mechanism works)
                        raise
                        logging.info("Request from task queue failed. Sending back 500 error.")

            else:
                logging.info("Not a valid email address. Not continuing.")


class SettingsRefresh(UtilitiesBase):
    def contactsJSON(self):
        taskqueue.add(url="/tasks/contactsjson", params={'s_key': self.e.websafe}, queue_name="backend")


class SettingsSearch(UtilitiesBase):
    def search(self, index_name, expr_list, query, search_function, query_cursor=None, entity_return=False,
               return_all=False):
        # query string looks like 'job tag:"very important" sent < 2011-02-28'

        if query_cursor == None:
            query_cursor = search.Cursor()
        elif isinstance(query_cursor, (str, unicode, basestring)):
            query_cursor = search.Cursor(web_safe_string=query_cursor)

        # construct the sort options
        sort_opts = search.SortOptions(expressions=expr_list)

        query_options = search.QueryOptions(
            cursor=query_cursor,
            limit=_NUM_RESULTS,
            sort_options=sort_opts)

        # Adding settings key to query (AND is mandatory to ensure that you cannot access other organizations' data)
        add_settings_query = "settings:" + self.e.websafe
        if query == "":
            query += add_settings_query

        elif add_settings_query not in query:
            query += " AND " + add_settings_query

        query_obj = search.Query(query_string=query, options=query_options)

        search_results = search.Index(name=index_name).search(query=query_obj)

        if entity_return == True and return_all == False:
            new_cursor = None
            if search_results.cursor != None:
                new_cursor = search_results.cursor.web_safe_string

            return [searchToEntities(search_results), new_cursor]

        elif return_all == True:
            return searchReturnAll(query, search_results, settings=self.e, search_function=search_function,
                                   entity_return=entity_return)

        else:
            return [search_results, search_results.cursor]

    def contact(self, query, **kwargs):
        expr_list = [search.SortExpression(
            expression="name", default_value='',
            direction=search.SortExpression.ASCENDING)]

        search_function = self.e.search.contact

        return self.search(index_name=_CONTACT_SEARCH_INDEX, expr_list=expr_list, query=query,
                           search_function=search_function, **kwargs)

    def deposit(self, query, **kwargs):

        expr_list = [search.SortExpression(
            expression="created", default_value=0,
            direction=search.SortExpression.DESCENDING)]

        search_function = self.e.search.deposit

        return self.search(index_name=_DEPOSIT_SEARCH_INDEX, expr_list=expr_list, query=query,
                           search_function=search_function, **kwargs)

    def donation(self, query, **kwargs):

        expr_list = [search.SortExpression(
            expression="timesort", default_value=0,
            direction=search.SortExpression.DESCENDING)]

        search_function = self.e.search.donation

        return self.search(index_name=_DONATION_SEARCH_INDEX, expr_list=expr_list, query=query,
                           search_function=search_function, **kwargs)

    def individual(self, query, **kwargs):
        expr_list = [search.SortExpression(
            expression="name", default_value='',
            direction=search.SortExpression.ASCENDING)]

        search_function = self.e.search.individual

        return self.search(index_name=_INDIVIDUAL_SEARCH_INDEX, expr_list=expr_list, query=query,
                           search_function=search_function, **kwargs)

    def team(self, query, **kwargs):
        expr_list = [search.SortExpression(
            expression="name", default_value='',
            direction=search.SortExpression.ASCENDING)]

        search_function = self.e.search.team

        return self.search(index_name=_TEAM_SEARCH_INDEX, expr_list=expr_list, query=query,
                           search_function=search_function, **kwargs)


## -- Contact Classes -- ##
class ContactCreate(UtilitiesBase):
    def impression(self, impression, notes):
        new_impression = models.Impression()

        new_impression.contact = self.e.key
        new_impression.impression = impression
        new_impression.notes = notes

        new_impression.put()


class ContactData(UtilitiesBase):
    @property
    def all_donations(self):
        q = models.Donation.gql("WHERE contact = :c ORDER BY donation_date DESC", s=self.e.settings, c=self.e.key)
        return q

    @property
    def all_impressions(self):
        q = models.Impression.gql("WHERE contact = :c ORDER BY creation_date DESC", c=self.e.key)
        return q

    def annual_donations(self, year):
        year = int(year)
        year_start = datetime.datetime(year, 1, 1)
        year_end = datetime.datetime(year + 1, 1, 1)

        return models.Donation.gql(
            "WHERE contact = :c AND donation_date >= :year_start AND donation_date < :year_end ORDER BY donation_date ASC",
            c=self.e.key, year_start=year_start, year_end=year_end)

    def donations(self, query_cursor):
        query = self.all_donations
        return queryCursorDB(query, query_cursor)

    @property
    def donation_total(self):
        donation_total = toDecimal(0)
        for d in self.all_donations:
            donation_total += d.confirmation_amount

        return donation_total

    @property
    def recurring_donation_total(self):
        donation_total = toDecimal(0)

        query = models.Donation.gql("WHERE contact = :c AND isRecurring = :r", c=self.e.key, r=True)
        for d in query:
            donation_total += d.amount_donated

        return donation_total

    def impressions(self, query_cursor):
        query = self.all_impressions
        return queryCursorDB(query, query_cursor)

    @property
    def number_donations(self):
        return int(gqlCount(self.all_donations))


class ContactSearch(UtilitiesBase):
    def createDocument(self):
        c = self.e

        email = ' '.join(c.email)

        document = search.Document(doc_id=c.websafe,
                                   fields=[search.TextField(name='contact_key', value=c.websafe),
                                           search.TextField(name='name', value=c.name),
                                           search.TextField(name='email', value=email),

                                           search.NumberField(name='total_donated', value=float(c.data.donation_total)),
                                           search.NumberField(name='number_donations',
                                                              value=int(c.data.number_donations)),

                                           search.TextField(name='phone', value=c.phone),

                                           search.TextField(name='street', value=c.address[0]),
                                           search.TextField(name='city', value=c.address[1]),
                                           search.TextField(name='state', value=c.address[2]),
                                           search.TextField(name='zip', value=c.address[3]),

                                           search.DateField(name='created', value=c.creation_date),
                                           search.TextField(name='settings', value=c.settings.urlsafe())
                                           ])

        return document

    def index(self):
        # Updates search index of this entity or creates new one if it doesn't exist
        index = search.Index(name=_CONTACT_SEARCH_INDEX)

        # Creating the new index
        try:
            doc = self.createDocument()
            index.put(doc)

        except Exception as e:
            logging.error("Failed creating index on contact key:" + self.e.websafe + " because: " + str(e))
            self.error(500)


## -- Deposit Classes -- ##
class DepositSearch(UtilitiesBase):
    def createDocument(self):
        de = self.e

        document = search.Document(doc_id=de.websafe,
                                   fields=[search.TextField(name='deposit_key', value=de.websafe),
                                           search.TextField(name='time_deposited_string', value=de.time_deposited),
                                           search.DateField(name='created', value=de.creation_date),
                                           search.TextField(name='settings', value=de.settings.urlsafe()),
                                           ])

        return document

    def index(self):
        # Updates search index of this entity or creates new one if it doesn't exist
        index = search.Index(name=_DEPOSIT_SEARCH_INDEX)

        # Creating the new index
        try:
            doc = self.createDocument()
            index.put(doc)

        except Exception as e:
            logging.error("Failed creating index on deposit key:" + self.e.websafe + " because: " + str(e))
            self.error(500)


## -- Donation Classes -- ##
class DonationAssign(UtilitiesBase):
    ## -- Associating Donations With Team/Individual -- ##
    def associateIndividual(self, individual_key, writeback):
        if self.e.individual != individual_key:
            # Just to make sure the association is actually changed - instead of marking the same value as it was before
            try:
                message = "Donation " + self.e.websafe + " associated with individual " + str(
                    individual_key.urlsafe()) + "."
                logging.info(message)
            except:
                pass

            self.e.individual = individual_key

        if writeback == True:
            self.e.put()

    def associateTeam(self, team_key, writeback):
        if self.e.team != team_key:
            # Just to make sure the association is actually changed - instead of marking the same value as it was before
            try:
                message = "Donation " + self.e.websafe + " associated with team " + str(team_key.urlsafe()) + "."
                logging.info(message)
            except:
                pass

            self.e.team = team_key

        if writeback == True:
            self.e.put()

    def disassociateIndividual(self, writeback):
        if self.e.individual != None:
            # Just to make sure the association is actually changed - instead of marking the same value as it was before
            message = "Donation " + self.e.websafe + " removed from individual " + str(
                self.e.individual.urlsafe()) + "."
            logging.info(message)

            self.e.individual = None

        if writeback == True:
            self.e.put()

    def disassociateTeam(self, writeback):
        if self.e.team != None:
            # Just to make sure the association is actually changed - instead of marking the same value as it was before
            message = "Donation " + self.e.websafe + " removed from team `" + str(self.e.team.urlsafe()) + "."
            logging.info(message)

            self.e.team = None

        if writeback == True:
            self.e.put()


class DonationConfirmation(UtilitiesBase):
    ## -- Confirmation Letter -- ##
    def email(self):
        d = self.e

        if d.email or d.email != ['']:

            message = mail.EmailMessage()
            if d.given_email:
                # Email address that came from PayPal
                message.to = d.given_email
            else:
                # Email address associated with contact
                message.to = d.email[0]

            ## TODO - is there any other way to get an organization's email address to appear if it's not verified?
            settings_name = d.settings.get().name
            if settings_name == "GHI":
                message.sender = "donate@globalhopeindia.org"
                message.subject = "Thanks for your donation!"
            else:
                message.sender = settings_name + " <mailer@ghidonations.appspotmail.com>"
                message.subject = settings_name + " - Thanks for your donation!"

            date = convertTime(d.donation_date).strftime("%B %d, %Y")
            s = d.settings.get()

            if d.individual:
                individual_name = d.individual.get().name
            elif d.team:
                individual_name = d.team.get().name
            else:
                individual_name = None

            template_variables = {"s": s, "d": d, "date": date, "individual_name": individual_name}

            who = "http://ghidonations.appspot.com"

            template_variables["see_url"] = d.confirmation.see_url(who)
            template_variables["print_url"] = d.confirmation.print_url(who)

            # Message body/HTML here
            message.html = template.render("pages/letters/thanks_email.html", template_variables)

            logging.info("Sending confirmation email to: " + d.email[0])

            # Adding to history
            logging.info("Confirmation email sent at " + currentTime())

            message.send()

        else:
            logging.info("No email address to send confirmation.  Not continuing.")

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
        taskqueue.add(url="/tasks/confirmation", params={'donation_key': self.e.websafe}, countdown=int(countdown_secs))


class DonationReview(UtilitiesBase):
    ## -- Review Queue -- ##
    def archive(self):
        self.e.reviewed = True
        self.e.put()

    def markUnreviewed(self):
        self.e.reviewed = False
        self.e.put()


class DonationSearch(UtilitiesBase):
    def createDocument(self):
        d = self.e
        c = d.contact.get()
        email = d.email[0]
        if not email:
            email = ""

        reviewed = "no"
        if d.reviewed == True:
            reviewed = "yes"

        team_key = ""
        if d.team:
            team_key = d.team.urlsafe()

        individual_key = ""
        if d.individual:
            individual_key = d.individual.urlsafe()

        time_seconds = int(time.mktime(d.donation_date.timetuple()))

        document = search.Document(doc_id=d.websafe,
                                   fields=[search.TextField(name='donation_key', value=d.websafe),

                                           search.DateField(name='time', value=d.donation_date),
                                           search.TextField(name='name', value=c.name),
                                           search.TextField(name='email', value=email),
                                           search.NumberField(name='amount', value=float(d.amount_donated)),
                                           search.TextField(name='type', value=d.payment_type),

                                           search.TextField(name='team', value=d.designated_team),
                                           search.TextField(name='individual', value=d.designated_individual),

                                           search.TextField(name='reviewed', value=reviewed),

                                           search.TextField(name='formatted_donation_date',
                                                            value=d.formatted_donation_date),

                                           search.TextField(name='contact_key', value=d.contact.urlsafe()),
                                           search.TextField(name='team_key', value=team_key),
                                           search.TextField(name='individual_key', value=individual_key),
                                           search.TextField(name='settings', value=d.settings.urlsafe()),
                                           search.NumberField(name='timesort', value=time_seconds),
                                           ])

        return document

    def index(self):
        # Updates search index of this entity or creates new one if it doesn't exist
        index = search.Index(name=_DONATION_SEARCH_INDEX)

        # Creating the new index
        try:
            doc = self.createDocument()
            index.put(doc)

        except Exception as e:
            logging.error("Failed creating index on donation key:" + self.e.websafe + " because: " + str(e))
            self.error(500)


## -- Individual Classes -- ##
class IndividualData(UtilitiesBase):
    @property
    def donation_total(self):
        memcache_key = "idtotal" + self.e.websafe

        def get_item():
            settings = self.e.settings
            individual_key = self.e.key

            q = models.Donation.gql("WHERE individual = :i", s=settings, i=individual_key)
            donations = qCache(q)

            donation_total = toDecimal(0)

            for d in donations:
                donation_total += d.amount_donated

            return str(donation_total)

        item = cache(memcache_key, get_item)
        return toDecimal(item)

    @property
    def donations(self):
        q = models.Donation.gql("WHERE individual = :i ORDER BY donation_date DESC", i=self.e.key)
        return qCache(q)

    def getTeamList(self, team):
        query = models.TeamList.gql("WHERE individual = :i AND team = :t", i=self.e.key, t=team)
        try:
            return query.fetch(1)[0]
        except:
            raise Exception("No individual-team pair found.")

    def info(self, team):
        memcache_key = "info" + team.urlsafe() + self.e.websafe

        def get_item():
            if self.e.photo:
                image_url = images.get_serving_url(self.e.photo, 150, secure_url=True)
            else:
                image_url = "https://ghidonations.appspot.com/images/face150.jpg"

            tl = self.getTeamList(team)

            percentage = None
            message = None
            if self.e.show_progress_bar:
                percentage = int(float(tl.data.donation_total / tl.fundraise_amt) * 100)

                if percentage > 100:
                    percentage = 100
                elif percentage < 0:
                    percentage = 0

                message = str(percentage) + "% to goal of $" + str(tl.fundraise_amt)

            return [image_url, self.e.name, self.e.description, percentage, message]

        return cache(memcache_key, get_item)

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

    @property
    def readable_team_names(self):
        team_names = ""
        tl_list = self.e.teamlist_entities
        for tl in tl_list:
            team_names += tl.team_name + ", "

        return team_names

    @property
    def search_team_list(self):
        search_list = ""

        for tl in self.teams:
            search_list += " " + tl.team.urlsafe()

        return search_list

    @property
    def teams(self):
        q = models.TeamList.gql("WHERE individual = :i", i=self.e.key)
        return q

    @property
    def team_list(self):
        teams_dict = {}

        for tl in self.teams:
            array = [tl.team.get().name, str(tl.fundraise_amt)]
            teams_dict[tl.team.urlsafe()] = array

        return teams_dict

    @property
    def team_json(self):
        return json.dumps(self.team_list)


class IndividualSearch(UtilitiesBase):
    def createDocument(self):
        i = self.e

        email = "" if not i.email else i.email

        document = search.Document(doc_id=i.websafe,
                                   fields=[search.TextField(name='individual_key', value=i.websafe),

                                           search.TextField(name='name', value=i.name),
                                           search.TextField(name='email', value=email),

                                           search.TextField(name='team', value=i.data.readable_team_names),
                                           search.NumberField(name='raised', value=float(i.data.donation_total)),

                                           search.DateField(name='created', value=i.creation_date),
                                           search.TextField(name='team_key', value=i.data.search_team_list),
                                           search.TextField(name='settings', value=i.settings.urlsafe()),
                                           ])

        return document

    def index(self):
        # Updates search index of this entity or creates new one if it doesn't exist
        index = search.Index(name=_INDIVIDUAL_SEARCH_INDEX)

        # Creating the new index
        try:
            doc = self.createDocument()
            index.put(doc)

        except Exception as e:
            logging.error("Failed creating index on individual key:" + self.e.websafe + " because: " + str(e))
            self.error(500)


## -- Team Classes -- ##
class TeamData(UtilitiesBase):
    @property
    def donations(self):
        q = models.Donation.gql("WHERE team = :t ORDER BY donation_date", s=self.e.settings, t=self.e.key)
        return qCache(q)

    @property
    def donation_total(self):
        team_key = self.e.key
        memcache_key = "tdtotal" + team_key.urlsafe()

        def get_item():
            settings = self.e.settings

            q = models.Donation.gql("WHERE team = :t", s=settings, t=team_key)
            donations = qCache(q)

            donation_total = toDecimal(0)

            for d in donations:
                donation_total += d.amount_donated

            return str(donation_total)

        item = cache(memcache_key, get_item)
        return toDecimal(item)

    @property
    def members(self):
        q = models.TeamList.gql("WHERE team = :t ORDER BY sort_name", t=self.e.key)
        return qCache(q)

    @property
    def members_public_donation_page(self):
        # Returns members that indicated that they want to be included
        # in the public donation page
        q = models.TeamList.gql("WHERE team = :t AND show_donation_page != :s ORDER BY show_donation_page, sort_name",
                                t=self.e.key, s=False)
        return qCache(q)

    @property
    def members_dict(self):
        memcache_key = "teammembersdict" + self.e.websafe
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
        memcache_key = "teammembers" + self.e.websafe

        def get_item():
            members = self.members

            return [[tl.individual_name, tl.individual.get().data.photo_url, tl.individual.urlsafe()] for tl in members]

        return cache(memcache_key, get_item)

    @property
    def public_members_list(self):
        memcache_key = "publicteammembers" + self.e.websafe

        def get_item():
            members = self.members_public_donation_page

            return [[tl.individual_name, tl.individual.get().data.photo_url, tl.individual.urlsafe()] for tl in members]

        return cache(memcache_key, get_item)


class TeamSearch(UtilitiesBase):
    def createDocument(self):
        t = self.e

        document = search.Document(doc_id=t.websafe,
                                   fields=[search.TextField(name='team_key', value=t.websafe),
                                           search.TextField(name='name', value=t.name),
                                           search.TextField(name='donation_total', value=str(t.data.donation_total)),
                                           search.DateField(name='created', value=t.creation_date),
                                           search.TextField(name='settings', value=t.settings.urlsafe()),
                                           ])

        return document

    def index(self):
        # Updates search index of this entity or creates new one if it doesn't exist
        index = search.Index(name=_TEAM_SEARCH_INDEX)

        # Creating the new index
        try:
            doc = self.createDocument()
            index.put(doc)

        except Exception as e:
            logging.error("Failed creating index on team key:" + self.e.websafe + " because: " + str(e))
            self.error(500)


class TeamListData(UtilitiesBase):
    @property
    def donations(self):
        i = self.e.individual.get()
        q = models.Donation.gql("WHERE team = :t AND individual = :i", s=i.settings, t=self.e.team, i=i.key)
        return qCache(q)

    @property
    def donation_total(self):
        i = self.e.individual.get()
        memcache_key = "dtotal" + self.e.team.urlsafe() + i.key.urlsafe()

        def get_item():
            q = self.donations
            # donations = tools.qCache(q)
            donations = q

            donation_total = toDecimal(0)

            for d in donations:
                donation_total += d.amount_donated

            return str(donation_total)

        item = cache(memcache_key, get_item)
        return toDecimal(item)

    @property
    def individual_email(self):
        return self.individual.get().email

    @property
    def individual_key(self):
        return self.individual.urlsafe()

    @property
    def team_websafe(self):
        return self.team.urlsafe()


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

class EST(datetime.tzinfo):
    def utcoffset(self, dt):
        return datetime.timedelta(hours=-4, minutes=0)

    def tzname(self, dt):
        return "GMT -4"

    def dst(self, dt):
        return datetime.timedelta(0)


class UTC(datetime.tzinfo):
    def utcoffset(self, dt):
        return datetime.timedelta(0)

    def tzname(self, dt):
        return "UTC"

    def dst(self, dt):
        return datetime.timedelta(0)
