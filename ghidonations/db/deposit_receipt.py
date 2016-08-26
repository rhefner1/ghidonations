from ghidonations import tools
from google.appengine.api import search
from google.appengine.api import taskqueue
from google.appengine.ext import ndb

_DEPOSIT_SEARCH_INDEX = "deposit"


class DepositReceipt(ndb.Expando):
    entity_keys = ndb.KeyProperty(repeated=True)

    settings = ndb.KeyProperty()
    time_deposited = ndb.StringProperty()

    creation_date = ndb.DateTimeProperty(auto_now_add=True)

    @property
    def search(self):
        return tools.DepositSearch(self)

    @property
    def websafe(self):
        return self.key.urlsafe()

    @classmethod
    def _post_put_hook(cls, future):
        e = future.get_result().get()
        taskqueue.add(url="/tasks/delayindexing", params={'e': e.websafe}, queue_name="delayindexing")

    @classmethod
    def _pre_delete_hook(cls, key):
        e = key.get()

        # Delete search index
        index = search.Index(name=_DEPOSIT_SEARCH_INDEX)
        index.delete(e.websafe)
