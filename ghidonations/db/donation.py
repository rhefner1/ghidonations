import datetime

from ghidonations import tools
from ghidonations.tools.util import DecimalProperty
from google.appengine.api import memcache, taskqueue
from google.appengine.api import search
from google.appengine.ext import ndb

_DONATION_SEARCH_INDEX = "donation"


class Donation(ndb.Expando):
    contact = ndb.KeyProperty()
    reviewed = ndb.BooleanProperty(default=False)

    # Only for deposited donations
    deposited = ndb.BooleanProperty()

    # Determines which account this donation is for - settings key
    settings = ndb.KeyProperty()

    # How much is this donation worth?
    amount_donated = DecimalProperty()
    confirmation_amount = DecimalProperty()

    # Is this a recurring donation
    isRecurring = ndb.BooleanProperty(default=False)

    # Whether it's recurring, one-time, or offline
    payment_type = ndb.StringProperty()

    # Special notes from PayPal custom field
    special_notes = ndb.TextProperty(indexed=True)

    # All recurring donations have the same ID; one-time of course
    # is unique to that payment
    payment_id = ndb.StringProperty()

    # Who to associate this donation to (keys)
    team = ndb.KeyProperty()
    individual = ndb.KeyProperty()

    # Sets the time that the donation was placed
    donation_date = ndb.DateTimeProperty(auto_now_add=True)

    # IPN original data
    ipn_data = ndb.TextProperty()

    # Used for debugging purposes to see who actually gave the donation
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

    def update(self, notes, team_key, individual_key, add_deposit, donation_date):
        # Get self data entity from datastore

        if team_key == "general":
            # If they completely disassociated the self (back to General Fund), clear out team and individual keys
            self.assign.disassociate_team(False)
            self.assign.disassociate_individual(False)

        else:
            # The team has isn't general, so associate it
            self.assign.associate_team(team_key, False)

            if individual_key == "none" or not individual_key:
                # Eiither part of General fund or in a team without a specific individual
                self.assign.disassociate_individual(False)

            else:
                # Associate individual
                self.assign.associate_individual(individual_key, False)

        if notes != str(self.special_notes):
            if not notes or notes == "":
                notes = "None"
            self.special_notes = notes

        # if add_deposit == False:
        #     #Make this value none to remove it from deposits window
        #     add_deposit = None

        # if add_deposit != self.deposited:
        #     self.deposited = add_deposit

        if donation_date:
            self.donation_date = datetime.datetime(donation_date.year, donation_date.month, donation_date.day)

        # And now to put that donation back in the datastore
        self.put()

    @classmethod
    def _post_put_hook(cls, future):
        e = future.get_result().get()
        memcache.delete("numopen" + e.settings.urlsafe())
        memcache.delete("owh" + e.settings.urlsafe())

        if e.team:
            memcache.delete("tdtotal" + e.team.urlsafe())

        if e.team and e.individual:
            memcache.delete("dtotal" + e.team.urlsafe() + e.individual.urlsafe())
            memcache.delete("idtotal" + e.individual.urlsafe())
            memcache.delete("info" + e.team.urlsafe() + e.individual.urlsafe())

            taskqueue.add(url="/tasks/delayindexing", params={'e': e.team.urlsafe()}, countdown=2,
                          queue_name="delayindexing")
            taskqueue.add(url="/tasks/delayindexing", params={'e': e.individual.urlsafe()}, countdown=2,
                          queue_name="delayindexing")

        taskqueue.add(url="/tasks/delayindexing", params={'e': e.websafe}, queue_name="delayindexing")

    @classmethod
    def _pre_delete_hook(cls, key):
        e = key.get()

        if e.team and e.individual:
            memcache.delete("tdtotal" + e.team.urlsafe())
            memcache.delete("idtotal" + e.individual.urlsafe())
            memcache.delete("info" + e.team.urlsafe() + e.individual.urlsafe())

            taskqueue.add(url="/tasks/delayindexing", params={'e': e.team.urlsafe()}, countdown=2,
                          queue_name="delayindexing")
            taskqueue.add(url="/tasks/delayindexing", params={'e': e.individual.urlsafe()}, countdown=2,
                          queue_name="delayindexing")

        # Delete search index
        index = search.Index(name=_DONATION_SEARCH_INDEX)
        index.delete(e.websafe)
