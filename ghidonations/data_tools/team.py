import logging

from ghidonations.data_tools.base import UtilitiesBase
from ghidonations.db.donation import Donation
from ghidonations.db.team_list import TeamList
from ghidonations.tools.memcache import q_cache, cache
from ghidonations.tools.util import to_decimal
from google.appengine.api import search

TEAM_SEARCH_INDEX = "team"


class TeamData(UtilitiesBase):
    @property
    def donations(self):
        q = Donation.gql("WHERE team = :t ORDER BY donation_date", s=self.e.settings, t=self.e.key)
        return q_cache(q)

    @property
    def donation_total(self):
        team_key = self.e.key
        memcache_key = "tdtotal" + team_key.urlsafe()

        def get_item():
            settings = self.e.settings

            q = Donation.gql("WHERE team = :t", s=settings, t=team_key)
            donations = q_cache(q)

            donation_total = to_decimal(0)

            for d in donations:
                donation_total += d.amount_donated

            return str(donation_total)

        item = cache(memcache_key, get_item)
        return to_decimal(item)

    @property
    def members(self):
        q = TeamList.gql("WHERE team = :t ORDER BY sort_name", t=self.e.key)
        return q_cache(q)

    @property
    def members_public_donation_page(self):
        # Returns members that indicated that they want to be included
        # in the public donation page
        q = TeamList.gql("WHERE team = :t AND show_donation_page != :s ORDER BY show_donation_page, sort_name",
                         t=self.e.key, s=False)
        return q_cache(q)

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
    def create_document(self):
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
        index = search.Index(name=TEAM_SEARCH_INDEX)

        # Creating the new index
        try:
            doc = self.create_document()
            index.put(doc)

        except Exception as e:
            logging.error("Failed creating index on team key:" + self.e.websafe + " because: " + str(e))
            self.error(500)


class TeamListData(UtilitiesBase):
    @property
    def donations(self):
        i = self.e.individual.get()
        q = Donation.gql("WHERE team = :t AND individual = :i", s=i.settings, t=self.e.team, i=i.key)
        return q_cache(q)

    @property
    def donation_total(self):
        i = self.e.individual.get()
        memcache_key = "dtotal" + self.e.team.urlsafe() + i.key.urlsafe()

        def get_item():
            q = self.donations
            # donations = tools.qCache(q)
            donations = q

            donation_total = to_decimal(0)

            for d in donations:
                donation_total += d.amount_donated

            return str(donation_total)

        item = cache(memcache_key, get_item)
        return to_decimal(item)

    @property
    def individual_email(self):
        return self.individual.get().email

    @property
    def individual_key(self):
        return self.individual.urlsafe()

    @property
    def team_websafe(self):
        return self.team.urlsafe()
