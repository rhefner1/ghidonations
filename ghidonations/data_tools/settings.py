import json
import logging

from ghidonations.data_tools.base import UtilitiesBase
from ghidonations.data_tools.contact import CONTACT_SEARCH_INDEX
from ghidonations.data_tools.deposit import DEPOSIT_SEARCH_INDEX
from ghidonations.data_tools.donation import DONATION_SEARCH_INDEX
from ghidonations.data_tools.individual import INDIVIDUAL_SEARCH_INDEX
from ghidonations.data_tools.team import TEAM_SEARCH_INDEX
from ghidonations.db.contact import Contact
from ghidonations.db.deposit_receipt import DepositReceipt
from ghidonations.db.donation import Donation
from ghidonations.db.individual import Individual
from ghidonations.db.team import Team
from ghidonations.db.team_list import TeamList
from ghidonations.tools.memcache import gql_count, cache, q_cache, get_key
from ghidonations.tools.search import search_to_entities, search_return_all
from ghidonations.tools.util import current_time, to_decimal, query_cursor_db, is_email_address, get_key
from google.appengine.api import taskqueue, mail, memcache, search
from mailsnake import MailSnake

NUM_RESULTS = 15


class SettingsCreate(UtilitiesBase):
    def contact(self, name, email=None, phone=None, address=None, notes=None, add_mc=False):
        logging.info("Creating contact for: " + name)
        if name:
            new_contact = Contact()
            new_contact.name = name
            new_contact.settings = self.e.key

            if not address or address == "":
                address = ['', '', '', '']
            if not notes or notes == "None":
                notes = ""
            if not email or email == "None":
                email = [""]
            if isinstance(email, basestring):
                email = [email]
            if not phone or phone == "None":
                phone = ""

            new_contact.email = email
            new_contact.phone = phone
            new_contact.address = address
            new_contact.notes = notes

            # Log the contact
            logging.info("Contact created.")

            new_contact.put()

            if add_mc:
                for e in email:
                    if e and e != "":
                        # Add new contact to Mailchimp
                        self.e.mailchimp.add(e, name, False)

            return new_contact.key
        else:
            logging.error("Cannot create contact because there is not a name.")

    def deposit_receipt(self, entity_keys):
        new_deposit = DepositReceipt()

        new_deposit.entity_keys = entity_keys
        new_deposit.settings = self.e.key
        new_deposit.time_deposited = current_time()

        new_deposit.put()

    def donation(self, name, email, amount_donated, payment_type, confirmation_amount=None, phone=None, address=None,
                 team_key=None, individual_key=None, add_deposit=True, payment_id=None, special_notes=None,
                 email_subscr=False, ipn_data=None, contact_key=None):
        if not confirmation_amount:
            confirmation_amount = amount_donated

        # All variables being passed as either string or integer
        new_donation = Donation()
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

        new_donation.amount_donated = to_decimal(amount_donated)
        new_donation.confirmation_amount = to_decimal(confirmation_amount)

        if add_deposit is True:
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

            if special_notes:
                email = mail.EmailMessage()
                email.sender = "GHI Donations <mailer@ghidonations.appspotmail.com>"
                email.subject = "New Donation with Note"
                email.to = self.e.email

                message = ('A new note was received from {name} for ${confirmation_amount} ({payment_type} donation): '
                           '<br><strong>{special_notes}</strong> <br><br>'
                           '<br><br>You can view this donation at <a href="'
                           'https://ghidonations.appspot.com/#contact?c={contact_key}">'
                           'https://ghidonations.appspot.com/contact?c={contact_key}</a>.<br><br>Thanks!')

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
        new_individual = Individual()

        new_individual.name = name
        new_individual.settings = self.e.key
        new_individual.admin = bool(admin)
        new_individual.description = ("Thank you for supporting my short-term mission trip to India. Your prayer and "
                                      "financial support is greatly needed and appreciated. Thanks for helping make "
                                      "it possible for me to go join God in His work in India.")

        if email:
            new_individual.email = email
            new_individual.password = password

        new_individual.put()

        new_tl = TeamList()
        new_tl.individual = new_individual.key
        new_tl.team = team_key
        new_tl.fundraise_amt = to_decimal("2900")
        new_tl.sort_name = name

        new_tl.put()

        memcache.delete("teammembersdict" + team_key.urlsafe())

        logging.info("Individual created.")
        return new_individual.key

    def recurring_donation(self, payment_id, duration, ipn_data=None):
        new_recurring = Donation()
        new_recurring.payment_id = payment_id
        new_recurring.duration = duration
        new_recurring.ipn_data = ipn_data

        new_recurring.put()

    def team(self, name):
        new_team = Team()
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
        q = Contact.gql("WHERE settings = :s ORDER BY name", s=self.e.key)
        return q

    @property
    def all_deposits(self):
        q = DepositReceipt.gql("WHERE settings = :s ORDER BY creation_date DESC", s=self.e.key)
        return q

    @property
    def all_donations(self):
        q = Donation.gql("WHERE settings = :s ORDER BY donation_date DESC", s=self.e.key)
        return q

    @property
    def all_individuals(self):
        q = Individual.gql("WHERE settings = :k ORDER BY name ASC", k=self.e.key)
        return q

    @property
    def all_teams(self):
        q = Team.gql("WHERE settings = :k ORDER BY name", k=self.e.key)
        return q

    def contacts(self, query_cursor):
        query = self.all_contacts
        return query_cursor_db(query, query_cursor)

    def deposits(self, query_cursor):
        query = self.all_deposits
        return query_cursor_db(query, query_cursor)

    @property
    def display_teams(self):
        q = Team.gql("WHERE settings = :k AND show_team = True ORDER BY name", k=self.e.key)
        return q

    def donations(self, query_cursor):
        query = self.all_donations
        return query_cursor_db(query, query_cursor)

    def individuals(self, query_cursor):
        query = self.all_individuals
        return query_cursor_db(query, query_cursor)

    @property
    def num_open_donations(self):
        memcache_key = "numopen" + self.e.websafe

        def get_item():
            query = Donation.gql("WHERE reviewed = :c AND settings = :s ORDER BY donation_date DESC", c=False,
                                 s=self.e.key)
            return gql_count(query)

        return cache(memcache_key, get_item)

    def open_donations(self, query_cursor):
        query = Donation.gql("WHERE reviewed = :c AND settings = :s ORDER BY donation_date DESC", c=False,
                             s=self.e.key)
        return query_cursor_db(query, query_cursor)

    @property
    def recurring_donors(self):
        donors_dict = {}
        query = Donation.gql("WHERE settings = :s AND isRecurring = :r", s=self.e.key, r=True)

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
        info = Donation.gql("WHERE payment_id = :id", id=payment_id).fetch(1)[0]
        return info

    def team_donors(self, team_key):
        donors = []
        donations = Donation.gql("WHERE team = :t", t=team_key)
        for d in donations:
            # if d.name not in donors:
            donors.append(d.contact.get())

        return donors

    @property
    def teams_dict(self):
        memcache_key = "teamsdict" + self.e.websafe

        def get_item():
            teams = Team.gql("WHERE settings = :k AND show_team = :s", k=self.e.key, s=True)

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
        return query_cursor_db(query, query_cursor)

    @property
    def undeposited_donations(self):
        q = Donation.gql("WHERE settings = :s AND deposited = :d ORDER BY donation_date DESC", s=self.e.key,
                         d=False)
        return q_cache(q)

    # Analytics
    @property
    def one_week_history(self):
        return json.loads(self.e.one_week_history)

    @property
    def one_month_history(self):
        return json.loads(self.e.one_month_history)

    # Contact autocomplete
    @property
    def contacts_json(self):
        memcache_key = "contacts" + self.e.websafe

        def get_item():
            return self.e.contacts_json

        return cache(memcache_key, get_item)


class SettingsDeposits(UtilitiesBase):
    def deposit(self, unicode_keys):
        # Changing all unicode keys into Key objects
        donation_keys = []
        for key in unicode_keys:
            donation_keys.append(get_key(key))

        self.e.create.deposit_receipt(donation_keys)

        for key in donation_keys:
            d = key.get()
            d.deposited = True
            d.put()

    def remove(self, unicode_keys):
        # Changing all unicode keys into Key objects
        donation_keys = []
        for key in unicode_keys:
            donation_keys.append(get_key(key))

        for key in donation_keys:
            d = key.get()
            d.deposited = None
            d.put()


class SettingsExists(UtilitiesBase):
    def _check_contact_email(self, email):
        try:
            if email == None or email == "":
                return [False, None]
            else:
                query = Contact.query(Contact.settings == self.e.key, Contact.email == email)

                if gql_count(query) != 0:
                    return [True, query.fetch(1)[0]]
                else:
                    return [False, None]

        except Exception:
            return [False, None]

    def _check_contact_name(self, name):
        try:
            query = Contact.query(Contact.settings == self.e.key, Contact.name == name)

            if gql_count(query) != 0:
                return [True, query.fetch(1)[0]]
            else:
                return [False, None]

        except Exception:
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
        if name and exists[0] is False:
            exists = self._check_contact_name(name)

        # If matched contact list only contains one item, take it out of list
        if isinstance(exists[1], list) and len(exists[1]) == 1:
            exists[1] = exists[1][0]

        return exists

    def entity(self, key):
        exists = True
        try:
            key.get()
        except Exception:
            exists = False

        return exists

    def individual(self, email):
        # Check if a user exists in the database - when creating new users
        try:
            user = Individual.gql("WHERE settings = :s AND email = :e", s=self.e.key, e=email)

            user_entity = user.fetch(1)[0]
            if user_entity:
                return [True, user_entity]
            else:
                return [False, None]

        except Exception:
            return [False, None]


class SettingsMailchimp(UtilitiesBase):
    def add(self, email, name, task_queue):
        if self.e.mc_use is True:
            # Check if the settings indicate to use Mailchimp

            if is_email_address(email):
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

                    if response is True:
                        logging.info("Email address added to database.")

                    elif response["code"] == 214:
                        logging.info("Already in database. No action required.")

                    else:
                        # Must be an error if not True and not error 214 - raise error
                        raise

                except Exception:
                    if task_queue is False:
                        # This is the original request, so add to task queue.
                        logging.error("An error occured contacting Mailchimp. Added to task queue to try again.")
                        taskqueue.add(url="/tasks/mailchimp",
                                      params={'email': email, 'name': name, 'settings': self.e.websafe},
                                      queue_name="mailchimp")

                    else:
                        # If this is coming from the task queue, fail it (so the task queue retry mechanism works)
                        logging.info("Request from task queue failed. Sending back 500 error.")
                        raise

            else:
                logging.info("Not a valid email address. Not continuing.")


class SettingsRefresh(UtilitiesBase):
    def contacts_json(self):
        taskqueue.add(url="/tasks/contactsjson", params={'s_key': self.e.websafe}, queue_name="backend")


class SettingsSearch(UtilitiesBase):
    def search(self, index_name, expr_list, query, search_function, query_cursor=None, entity_return=False,
               return_all=False):
        # query string looks like 'job tag:"very important" sent < 2011-02-28'

        if not query_cursor:
            query_cursor = search.Cursor()
        elif isinstance(query_cursor, (str, unicode, basestring)):
            query_cursor = search.Cursor(web_safe_string=query_cursor)

        # construct the sort options
        sort_opts = search.SortOptions(expressions=expr_list)

        query_options = search.QueryOptions(
            cursor=query_cursor,
            limit=NUM_RESULTS,
            sort_options=sort_opts)

        # Adding settings key to query (AND is mandatory to ensure that you cannot access other organizations' data)
        add_settings_query = "settings:" + self.e.websafe
        if query == "":
            query += add_settings_query

        elif add_settings_query not in query:
            query += " AND " + add_settings_query

        query_obj = search.Query(query_string=query, options=query_options)

        search_results = search.Index(name=index_name).search(query=query_obj)

        if entity_return is True and return_all is False:
            new_cursor = None
            if search_results.cursor:
                new_cursor = search_results.cursor.web_safe_string

            return [search_to_entities(search_results), new_cursor]

        elif return_all is True:
            return search_return_all(query, search_results, settings=self.e, search_function=search_function,
                                     entity_return=entity_return)

        else:
            return [search_results, search_results.cursor]

    def contact(self, query, **kwargs):
        expr_list = [search.SortExpression(
            expression="name", default_value='',
            direction=search.SortExpression.ASCENDING)]

        search_function = self.e.search.contact

        return self.search(index_name=CONTACT_SEARCH_INDEX, expr_list=expr_list, query=query,
                           search_function=search_function, **kwargs)

    def deposit(self, query, **kwargs):

        expr_list = [search.SortExpression(
            expression="created", default_value=0,
            direction=search.SortExpression.DESCENDING)]

        search_function = self.e.search.deposit

        return self.search(index_name=DEPOSIT_SEARCH_INDEX, expr_list=expr_list, query=query,
                           search_function=search_function, **kwargs)

    def donation(self, query, **kwargs):

        expr_list = [search.SortExpression(
            expression="timesort", default_value=0,
            direction=search.SortExpression.DESCENDING)]

        search_function = self.e.search.donation

        return self.search(index_name=DONATION_SEARCH_INDEX, expr_list=expr_list, query=query,
                           search_function=search_function, **kwargs)

    def individual(self, query, **kwargs):
        expr_list = [search.SortExpression(
            expression="name", default_value='',
            direction=search.SortExpression.ASCENDING)]

        search_function = self.e.search.individual

        return self.search(index_name=INDIVIDUAL_SEARCH_INDEX, expr_list=expr_list, query=query,
                           search_function=search_function, **kwargs)

    def team(self, query, **kwargs):
        expr_list = [search.SortExpression(
            expression="name", default_value='',
            direction=search.SortExpression.ASCENDING)]

        search_function = self.e.search.team

        return self.search(index_name=TEAM_SEARCH_INDEX, expr_list=expr_list, query=query,
                           search_function=search_function, **kwargs)
