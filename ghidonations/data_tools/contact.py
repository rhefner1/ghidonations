import datetime
import logging

from ghidonations.data_tools.base import UtilitiesBase
from ghidonations.db.donation import Donation
from ghidonations.db.impression import Impression
from ghidonations.tools.memcache import gql_count
from ghidonations.tools.util import query_cursor_db, to_decimal
from google.appengine.api import search

CONTACT_SEARCH_INDEX = "contact"


class ContactCreate(UtilitiesBase):
    def impression(self, impression, notes):
        new_impression = Impression()

        new_impression.contact = self.e.key
        new_impression.impression = impression
        new_impression.notes = notes

        new_impression.put()


class ContactData(UtilitiesBase):
    @property
    def all_donations(self):
        q = Donation.gql("WHERE contact = :c ORDER BY donation_date DESC", s=self.e.settings, c=self.e.key)
        return q

    @property
    def all_impressions(self):
        q = Impression.gql("WHERE contact = :c ORDER BY creation_date DESC", c=self.e.key)
        return q

    def annual_donations(self, year):
        year = int(year)
        year_start = datetime.datetime(year, 1, 1)
        year_end = datetime.datetime(year + 1, 1, 1)

        return Donation.gql(
            "WHERE contact = :c AND donation_date >= :year_start AND donation_date < :year_end ORDER BY donation_date ASC",
            c=self.e.key, year_start=year_start, year_end=year_end)

    def donations(self, query_cursor):
        query = self.all_donations
        return query_cursor_db(query, query_cursor)

    @property
    def donation_total(self):
        donation_total = to_decimal(0)
        for d in self.all_donations:
            donation_total += d.confirmation_amount

        return donation_total

    @property
    def recurring_donation_total(self):
        donation_total = to_decimal(0)

        query = Donation.gql("WHERE contact = :c AND isRecurring = :r", c=self.e.key, r=True)
        for d in query:
            donation_total += d.amount_donated

        return donation_total

    def impressions(self, query_cursor):
        query = self.all_impressions
        return query_cursor_db(query, query_cursor)

    @property
    def number_donations(self):
        return int(gql_count(self.all_donations))


class ContactSearch(UtilitiesBase):
    def create_document(self):
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
        index = search.Index(name=CONTACT_SEARCH_INDEX)

        # Creating the new index
        try:
            doc = self.create_document()
            index.put(doc)

        except Exception as e:
            logging.error("Failed creating index on contact key:" + self.e.websafe + " because: " + str(e))
            self.error(500)
