from google.appengine.ext import ndb


class GlobalSettings(ndb.Expando):
    cookie_key = ndb.StringProperty()
    gcs_bucket = ndb.StringProperty()
