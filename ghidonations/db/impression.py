from ghidonations import tools
from google.appengine.ext import ndb


class Impression(ndb.Expando):
    contact = ndb.KeyProperty()
    impression = ndb.StringProperty()
    notes = ndb.TextProperty(indexed=True)

    # Sets creation date
    creation_date = ndb.DateTimeProperty(auto_now_add=True)

    @property
    def formatted_creation_date(self):
        return tools.convertTime(self.creation_date).strftime("%b %d, %Y")

    @property
    def websafe(self):
        return self.key.urlsafe()
