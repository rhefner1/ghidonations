import logging, json, datetime
from decimal import *

#App Engine platform
from google.appengine.api import mail, memcache, datastore_errors, taskqueue
from google.appengine.ext import ndb, blobstore, deferred

#Search
from google.appengine.api import search

import GlobalUtilities as tools

_CONTACT_SEARCH_INDEX = "contact"
_DEPOSIT_SEARCH_INDEX = "deposit"
_DONATION_SEARCH_INDEX = "donation"
_INDIVIDUAL_SEARCH_INDEX = "individual"
_TEAM_SEARCH_INDEX = "team"

def reindexEntities(entity_list):
    # Donations refer back to contact data and need to have their search documents updated when a contact is updated
    for e in tools.qCache(entity_list):
        taskqueue.add(url="/tasks/delayindexing", params={'e' : e}, queue_name="delayindexing")

class DecimalProperty(ndb.StringProperty):
    def _validate(self, value):
        if not isinstance(value, (Decimal, str)):
            raise datastore_errors.BadValueError('Expected decimal or string, got %r' % (value,))

        return value

    def _to_base_type(self, value):
        return str(value)

    def _from_base_type(self, value):
        return tools.toDecimal(value)

###### ////// ------ Define datastore models ------ ////// ######
class Contact(ndb.Expando):
    #Standard information we need to know
    name = ndb.StringProperty()
    email = ndb.StringProperty(repeated=True)
    phone = ndb.StringProperty()
    address = ndb.StringProperty(repeated=True)
    notes = ndb.TextProperty(indexed=True)
    
    settings = ndb.KeyProperty()

    #Sets creation date
    creation_date = ndb.DateTimeProperty(auto_now_add=True)

    @property
    def address_json(self):
        return json.dumps(self.address)

    @property
    def address_formatted(self):
        a = self.address
        if not a == ["", "", "", ""]:
            return a[0] + "\n" + a[1] + ", " + a[2] + "  " + a[3]
        else:
            return ""

    @property
    def create(self):
        return tools.ContactCreate(self)

    @property
    def data(self):
        return tools.ContactData(self)

    @property
    def search(self):
        return tools.ContactSearch(self)

    @property
    def websafe(self):
        return self.key.urlsafe()

    ## -- Update contact -- ##
    def update(self, name, email, phone, notes, address):
        settings = self.settings.get()

        #Changing blank values to None
        if name == "":
            name = None
        if email == None:
            email = [""]

        if name != self.name and name != None:
            self.name = name

            # Reindexing donations on name change
            all_donations = Donation.query(Donation.settings == self.settings, Donation.contact == self.key)
            reindexEntities(all_donations)
            #deferred.defer( reindexEntities, entity_list=all_donations, countdown=2, _queue="backend" )

        if email != self.email:
            self.email = email
            
            if settings.mc_use:
                for e in email:
                    if e and e != "":
                        settings.mailchimp.add(e, name, False)

        if phone != self.phone:
            self.phone = phone

        if notes != str(self.notes):
            if notes == None:
                notes = ""
            self.notes = notes

        if address != self.address:
            if address != None and address != "" and address != "None":
                #If the address is something and is different than that on file
                self.address = address

        #And now to put that contact back in the datastore
        self.put()

    ## -- After Put -- ##
    @classmethod
    def _post_put_hook(self, future):
        e = future.get_result().get()
        memcache.delete("contacts" + e.settings.urlsafe())

        e.settings.get().refresh.contactsJSON()
        taskqueue.add(url="/tasks/delayindexing", params={'e' : e.websafe}, queue_name="delayindexing")

    ## -- Before Delete -- ##
    @classmethod
    def _pre_delete_hook(cls, key):
        e = key.get()

        # Delete search index
        index = search.Index(name=_CONTACT_SEARCH_INDEX)
        index.delete(e.websafe)

class DepositReceipt(ndb.Expando):
    entity_keys = ndb.KeyProperty(repeated=True)

    settings = ndb.KeyProperty()
    time_deposited = ndb.StringProperty()

    #Sets creation date
    creation_date = ndb.DateTimeProperty(auto_now_add=True)

    @property
    def search(self):
        return tools.DepositSearch(self)

    @property
    def websafe(self):
        return self.key.urlsafe()

    ## -- After Put -- ##
    @classmethod
    def _post_put_hook(self, future):
        e = future.get_result().get()
        taskqueue.add(url="/tasks/delayindexing", params={'e' : e.websafe}, queue_name="delayindexing")

     ## -- Before Delete -- ##
    @classmethod
    def _pre_delete_hook(cls, key):
        e = key.get()

        # Delete search index
        index = search.Index(name=_DEPOSIT_SEARCH_INDEX)
        index.delete(e.websafe)

class Donation(ndb.Expando):
    contact = ndb.KeyProperty()
    reviewed = ndb.BooleanProperty(default=False)

    #Only for deposited donations
    deposited = ndb.BooleanProperty()

    #Determines which account this donation is for - settings key
    settings = ndb.KeyProperty()

    #How much is this donation worth?
    amount_donated = DecimalProperty()
    confirmation_amount = DecimalProperty()

    #Is this a recurring donation
    isRecurring = ndb.BooleanProperty(default=False)

    #Whether it's recurring, one-time, or offline
    payment_type = ndb.StringProperty()

    #Special notes from PayPal custom field
    special_notes = ndb.TextProperty(indexed=True)

    #All recurring donations have the same ID; one-time of course
    #is unique to that payment
    payment_id = ndb.StringProperty()

    #Who to associate this donation to (keys)
    team = ndb.KeyProperty()
    individual = ndb.KeyProperty()
    
    #Sets the time that the donation was placed
    donation_date = ndb.DateTimeProperty(auto_now_add=True)

    #IPN original data
    ipn_data = ndb.TextProperty()

    #Used for debugging purposes to see who actually gave the donation
    given_name = ndb.StringProperty()
    given_email = ndb.StringProperty()

    @property
    def address(self):
        return self.contact.get().address_formatted

    @property
    def assign(self):
        return tools.DonationAssign(self)

    @property
    def confirmation(self):
        return tools.DonationConfirmation(self)

    @property
    def contact_url(self):
        return "#contact?c=" + self.contact.urlsafe()

    @property
    def designated_individual(self):
        if self.individual:
            return self.individual.get().name
        else:
            return None

    @property
    def designated_team(self):
        if self.team:
            return self.team.get().name
        else:
            return None

    @property
    def email(self):
        return self.contact.get().email

    @property
    def email_formatted(self):
        return tools.truncateEmail(self.email, is_list=True)

    @property
    def formatted_donation_date(self):
        return tools.convertTime(self.donation_date).strftime("%b %d, %Y")

    @property
    def name(self):
        return self.contact.get().name

    @property
    def review(self):
        return tools.DonationReview(self)

    @property
    def search(self):
        return tools.DonationSearch(self)

    @property
    def websafe(self):
        return self.key.urlsafe()

    ## -- Update donation -- ##
    def update(self, notes, team_key, individual_key, add_deposit, donation_date):
        #Get self data entity from datastore

        if team_key == "general":
        #If they completely disassociated the self (back to General Fund), clear out team and individual keys
            self.assign.disassociateTeam(False)
            self.assign.disassociateIndividual(False)

        else:
        #The team has isn't general, so associate it
            self.assign.associateTeam(team_key, False)

            if individual_key == "none" or individual_key == None:
            #Eiither part of General fund or in a team without a specific individual
                self.assign.disassociateIndividual(False)

            else:
            #Associate individual
                self.assign.associateIndividual(individual_key, False)
                
        if notes != str(self.special_notes):
            if notes == None or notes == "":
                notes = "None"
            self.special_notes = notes

        # if add_deposit == False:
        #     #Make this value none to remove it from deposits window
        #     add_deposit = None

        # if add_deposit != self.deposited:
        #     self.deposited = add_deposit

        if donation_date:
            self.donation_date = datetime.datetime(donation_date.year, donation_date.month, donation_date.day)

        #And now to put that donation back in the datastore
        self.put()

    ## -- After Put -- ##
    @classmethod
    def _post_put_hook(self, future):
        e = future.get_result().get()
        memcache.delete("numopen" + e.settings.urlsafe())
        memcache.delete("owh" + e.settings.urlsafe())

        if e.team:
            memcache.delete("tdtotal" + e.team.urlsafe())

        if e.team and e.individual:
            memcache.delete("dtotal" + e.team.urlsafe() + e.individual.urlsafe())
            memcache.delete("idtotal" + e.individual.urlsafe())
            memcache.delete("info" + e.team.urlsafe() + e.individual.urlsafe())

            taskqueue.add(url="/tasks/delayindexing", params={'e' : e.team.urlsafe()}, countdown=2, queue_name="delayindexing")
            taskqueue.add(url="/tasks/delayindexing", params={'e' : e.individual.urlsafe()}, countdown=2, queue_name="delayindexing")

        taskqueue.add(url="/tasks/delayindexing", params={'e' : e.websafe}, queue_name="delayindexing")

     ## -- Before Delete -- ##

    @classmethod
    def _pre_delete_hook(cls, key):
        e = key.get()

        if e.team and e.individual:
            memcache.delete("tdtotal" + e.team.urlsafe())
            memcache.delete("idtotal" + e.individual.urlsafe())
            memcache.delete("info" + e.team.urlsafe() + e.individual.urlsafe())

            taskqueue.add(url="/tasks/delayindexing", params={'e' : e.team.urlsafe()}, countdown=2, queue_name="delayindexing")
            taskqueue.add(url="/tasks/delayindexing", params={'e' : e.individual.urlsafe()}, countdown=2, queue_name="delayindexing")

        # Delete search index
        index = search.Index(name=_DONATION_SEARCH_INDEX)
        index.delete(e.websafe)

class Impression(ndb.Expando):
    contact = ndb.KeyProperty()
    impression = ndb.StringProperty()
    notes = ndb.TextProperty(indexed=True)

    #Sets creation date
    creation_date = ndb.DateTimeProperty(auto_now_add=True)

    @property
    def formatted_creation_date(self):
        return tools.convertTime(self.creation_date).strftime("%b %d, %Y")

    @property
    def websafe(self):
        return self.key.urlsafe()

class Individual(ndb.Expando):
    name = ndb.StringProperty()
    email = ndb.StringProperty()

    #Determines which account this person belongs to
    settings = ndb.KeyProperty()

    #Credentials
    admin = ndb.BooleanProperty()
    password = ndb.StringProperty()

    #Profile
    description = ndb.TextProperty()
    photo = ndb.StringProperty()

    #Sets creation date
    creation_date = ndb.DateTimeProperty(auto_now_add=True)

    @property
    def data(self):
        return tools.IndividualData(self)

    @property
    def teamlist_entities(self):
        q = TeamList.gql("WHERE individual = :i", i=self.key)
        return tools.qCache(q)

    @property
    def search(self):
        return tools.IndividualSearch(self)

    @property
    def show_donation_page(self):
        try:
            q = TeamList.gql("WHERE individual = :i", i=self.key)
            return q.fetch(1)[0].show_donation_page

        except:
            return False

    @property
    def websafe(self):
        return self.key.urlsafe()

    ## Currently not in use
    def email_user(self, msg_id):
        #Gives the user an email when something happens in their account
        if msg_id == 1:
            email_subject = "Recurring donation"
            email_message = "A new recurring donation was sent to you!"

        message = mail.EmailMessage()
        message.sender = "donate@globalhopeindia.org"
        message.subject = email_subject
        message.to = self.email

        #Message body here - determined from msg_id
        message.body = email_message

        logging.info("Sending alert email to: " + self.email)

        #Adding to history
        logging.info("Alert email sent at " + tools.currentTime())

        message.send()

    ## -- Update Individual -- #
    def update(self, name, email, team_list, description, change_image, password, show_donation_page):
        name_changed = False

        if name != self.name:
            self.name = name
            name_changed = True
        
        if email != self.email:
            self.email = email

        #Initializes DictDiffer object to tell differences from current dictionary to server-side one
        team = json.loads(team_list)
        dd = tools.DictDiffer(team, self.data.team_list)

        for key in dd.added():
            new_tl = TeamList()
            new_tl.individual = self.key
            new_tl.team = tools.getKey(key)
            new_tl.fundraise_amt = tools.toDecimal(team[key][1])

            new_tl.put()

        for key in dd.removed():
            query = TeamList.gql("WHERE team = :t AND individual = :i", t=tools.getKey(key), i=self.key)
            tl = query.fetch(1)[0]

            for d in tl.data.donations:
                d.team = None
                d.put()

            tl.key.delete()

        for key in dd.changed():
            query = TeamList.gql("WHERE team = :t AND individual = :i", t=tools.getKey(key), i=self.key)

            tl = query.fetch(1)[0]
            tl.fundraise_amt = tools.toDecimal(team[key][1])
            tl.put()

        if description != str(self.description):
            self.description = description

        if change_image != None:
        #If change_image = None, there isn't any change. If it isn't, it 
        #contains a 
            if self.photo != None:
                #Delete old blob to keep it from orphaning
                old_blobkey = self.photo
                old_blob = blobstore.BlobInfo.get(old_blobkey)
                old_blob.delete()

            self.photo = change_image

        if password != None and password != "" and self.password != password:
            self.password = password

        try:
            for tl in self.teamlist_entities:
                if show_donation_page != tl.show_donation_page:
                    tl.show_donation_page = show_donation_page
                
                if name_changed == True:
                    tl.sort_name = name

                tl.put()
        except:
            pass

        self.put()

    ## -- After put -- ##
    def _post_put_hook(self, future):
        e = future.get_result().get()

        deferred.defer(clear_team_memcache, e, _queue="backend")
            
        taskqueue.add(url="/tasks/delayindexing", params={'e' : e.websafe}, countdown=2, queue_name="delayindexing")

    ## -- Before Delete -- ##
    @classmethod
    def _pre_delete_hook(cls, key):
        i = key.get()

        #Removing this individual's association with donations
        for d in i.data.donations:
            d.team = None
            d.individual = None
            d.put()

        for tl in i.data.teams:
            memcache.delete("teammembers" + tl.team.urlsafe())
            memcache.delete("teammembersdict" + tl.team.urlsafe())

            tl.key.delete()

        # Delete search index
        index = search.Index(name=_INDIVIDUAL_SEARCH_INDEX)
        index.delete(i.websafe)

class Settings(ndb.Expando):
    name = ndb.StringProperty()
    email = ndb.StringProperty()

    #Mailchimp values
    mc_use = ndb.BooleanProperty()
    mc_apikey = ndb.StringProperty()
    mc_donorlist = ndb.StringProperty()

    #Impressions
    impressions = ndb.StringProperty(repeated=True)

    #PayPal
    paypal_id = ndb.StringProperty()

    #Donate page
    amount1 = ndb.IntegerProperty()
    amount2 = ndb.IntegerProperty()
    amount3 = ndb.IntegerProperty()
    amount4 = ndb.IntegerProperty()
    use_custom = ndb.BooleanProperty()

    donate_parent = ndb.StringProperty()

    #Confirmation letters
    confirmation_text = ndb.TextProperty()
    confirmation_info = ndb.TextProperty()
    confirmation_header = ndb.TextProperty()
    confirmation_footer = ndb.TextProperty()
    donor_report_text = ndb.TextProperty()

    #Contact JSON
    contacts_json = ndb.TextProperty()

    #Analytics
    one_week_history = ndb.TextProperty()
    one_month_history = ndb.TextProperty()

    #Sets creation date
    creation_date = ndb.DateTimeProperty(auto_now_add=True)  

    @property
    def create(self):
        return tools.SettingsCreate(self)

    @property
    def data(self):
        return tools.SettingsData(self)

    @property
    def exists(self):
        return tools.SettingsExists(self)

    @property
    def deposits(self):
        return tools.SettingsDeposits(self)

    @property
    def impressions_json(self):
        return json.dumps(self.impressions)

    @property
    def mailchimp(self):
        return tools.SettingsMailchimp(self)

    @property
    def refresh(self):
        return tools.SettingsRefresh(self)

    @property
    def search(self):
        return tools.SettingsSearch(self)

    ## -- Update -- ##
    def update(self, name, email, mc_use, mc_apikey, mc_donorlist, paypal_id, impressions, donate_parent, amount1, amount2, amount3, amount4, use_custom, confirmation_header, confirmation_info, confirmation_footer, confirmation_text, donor_report_text):
        s = self

        if name != s.name:
            s.name = name

        if email != s.email:
            s.email = email

        if mc_use != s.mc_use:
            s.mc_use = mc_use

        if mc_apikey != s.mc_apikey:
            s.mc_apikey = mc_apikey

        if mc_donorlist != s.mc_donorlist:
            s.mc_donorlist = mc_donorlist

        if paypal_id != s.paypal_id:
            s.paypal_id = paypal_id

        if impressions != s.impressions:
            s.impressions = impressions

        if donate_parent != s.donate_parent:
            s.donate_parent = donate_parent

        if int(amount1) != s.amount1:
            s.amount1 = int(amount1)

        if int(amount2) != s.amount2:
            s.amount2 = int(amount2)

        if int(amount3) != s.amount3:
            s.amount3 = int(amount3)

        if int(amount4) != s.amount4:
            s.amount4 = int(amount4)

        if use_custom != s.use_custom:
            s.use_custom = use_custom

        if confirmation_header != s.confirmation_header:
            s.confirmation_header = confirmation_header

        if confirmation_info != s.confirmation_info:
            s.confirmation_info = confirmation_info

        if confirmation_footer != s.confirmation_footer:
            s.confirmation_footer = confirmation_footer

        if confirmation_text != s.confirmation_text:
            s.confirmation_text = confirmation_text

        if donor_report_text != s.donor_report_text:
            s.donor_report_text = donor_report_text

        s.put()
              
    @property
    def websafe(self):
        return self.key.urlsafe()

class Team(ndb.Expando):
    name = ndb.StringProperty()
    settings = ndb.KeyProperty()
    show_team = ndb.BooleanProperty()
    
    #Sets creation date
    creation_date = ndb.DateTimeProperty(auto_now_add=True)

    @property
    def data(self):
        return tools.TeamData(self)

    @property
    def search(self):
        return tools.TeamSearch(self)

    @property
    def websafe(self):
        return self.key.urlsafe()

    ## -- Update -- ##
    def update(self, name, show_team):
        if name != self.name:
            self.name = name

        if show_team != self.show_team:
            self.show_team = show_team

        self.put()

    ## -- After put -- ##
    @classmethod
    def _post_put_hook(self, future):
        e = future.get_result().get()
        memcache.delete('allteams' + e.settings.urlsafe())
        memcache.delete("teammembers" + e.websafe)
        memcache.delete("teamsdict" + e.settings.urlsafe())

        #deferred.defer( tools.TeamSearch.updateDonations, base_entity=self, _queue="backend" )
        taskqueue.add(url="/tasks/delayindexing", params={'e' : e.websafe}, countdown=2, queue_name="delayindexing")      

    ## -- Before Deletion -- ##
    @classmethod
    def _pre_delete_hook(cls, key):
        t = key.get()
        logging.info("Deleting team:" + t.name)

        for tl in t.data.members:
            if tl:
            #Delete this team from all
                tl.key.delete()

        for d in t.data.donations:
            d.individual = None
            d.team = None
            d.put()

        # Delete search index
        index = search.Index(name=_TEAM_SEARCH_INDEX)
        index.delete(t.websafe)

class TeamList(ndb.Model):
    individual = ndb.KeyProperty()
    team = ndb.KeyProperty()
    fundraise_amt = DecimalProperty()

    #Show in public donation page
    show_donation_page = ndb.BooleanProperty()

    sort_name = ndb.StringProperty()

    @property
    def data(self):
        return tools.TeamListData(self)

    @property
    def individual_name(self):
        return self.individual.get().name

    @property 
    def team_name(self):
        return self.team.get().name

    @property
    def websafe(self):
        return self.key.urlsafe()

## -- Utilities -- ##
def clear_team_memcache(e):
    for t in e.data.teams:
        memcache.delete("teammembers" + t.team.urlsafe())
        memcache.delete("teammembersdict" + t.team.urlsafe())
        memcache.delete("info" + t.team.urlsafe() + e.websafe)