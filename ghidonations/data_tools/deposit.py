import logging

from ghidonations.data_tools.base import UtilitiesBase
from google.appengine.api import search

DEPOSIT_SEARCH_INDEX = "deposit"


class DepositSearch(UtilitiesBase):
    def create_document(self):
        de = self.e

        return search.Document(doc_id=de.websafe,
                               fields=[
                                   search.TextField(name='deposit_key', value=de.websafe),
                                   search.TextField(name='time_deposited_string', value=de.time_deposited),
                                   search.DateField(name='created', value=de.creation_date),
                                   search.TextField(name='settings', value=de.settings.urlsafe()),
                               ])

    def index(self):
        # Updates search index of this entity or creates new one if it doesn't exist
        index = search.Index(name=DEPOSIT_SEARCH_INDEX)

        # Creating the new index
        try:
            doc = self.create_document()
            index.put(doc)

        except Exception as e:
            logging.error("Failed creating index on deposit key:" + self.e.websafe + " because: " + str(e))
            self.error(500)
