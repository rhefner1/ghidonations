import json
import logging

from ghidonations.data_tools.base import UtilitiesBase
from ghidonations.db.donation import Donation
from ghidonations.db.team_list import TeamList
from ghidonations.tools.memcache import q_cache, cache
from ghidonations.tools.util import to_decimal
from google.appengine.api import images, search

INDIVIDUAL_SEARCH_INDEX = "individual"


class IndividualData(UtilitiesBase):
    @property
    def donation_total(self):
        memcache_key = "idtotal" + self.e.websafe

        def get_item():
            settings = self.e.settings
            individual_key = self.e.key

            q = Donation.gql("WHERE individual = :i", s=settings, i=individual_key)
            donations = q_cache(q)

            donation_total = to_decimal(0)

            for d in donations:
                donation_total += d.amount_donated

            return str(donation_total)

        item = cache(memcache_key, get_item)
        return to_decimal(item)

    @property
    def donations(self):
        q = Donation.gql("WHERE individual = :i ORDER BY donation_date DESC", i=self.e.key)
        return q_cache(q)

    def get_team_list(self, team):
        query = TeamList.gql("WHERE individual = :i AND team = :t", i=self.e.key, t=team)
        try:
            return query.fetch(1)[0]
        except Exception:
            raise Exception("No individual-team pair found.")

    def info(self, team):
        memcache_key = "info" + team.urlsafe() + self.e.websafe

        def get_item():
            if self.e.photo:
                image_url = images.get_serving_url(self.e.photo, 150, secure_url=True)
            else:
                image_url = "https://ghidonations.appspot.com/images/face150.jpg"

            tl = self.get_team_list(team)

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
        if self.e.photo:
            try:
                photo = images.get_serving_url(self.e.photo, 200, secure_url=True)
            except Exception:
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
        q = TeamList.gql("WHERE individual = :i", i=self.e.key)
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
    def create_document(self):
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
        index = search.Index(name=INDIVIDUAL_SEARCH_INDEX)

        # Creating the new index
        try:
            doc = self.create_document()
            index.put(doc)

        except Exception as e:
            logging.error("Failed creating index on individual key:" + self.e.websafe + " because: " + str(e))
            self.error(500)
