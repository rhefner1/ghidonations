import sys

import os

from gaesessions import SessionMiddleware
from ghidonations.tools import util
from google.appengine.api import memcache
from google.appengine.ext.appstats import recording

COOKIE_KEY = memcache.get("COOKIE_KEY")
GCS_BUCKET = memcache.get("GCS_BUCKET")

if not COOKIE_KEY or not GCS_BUCKET:
    global_settings = util.get_global_settings()

    COOKIE_KEY = global_settings.cookie_key.decode('base64')
    GCS_BUCKET = global_settings.gcs_bucket

    memcache.set("COOKIE_KEY", COOKIE_KEY)
    memcache.set("GCS_BUCKET", GCS_BUCKET)


def webapp_add_wsgi_middleware(app):
    app = SessionMiddleware(app, cookie_key=COOKIE_KEY)
    return app


def recording_add_wsgi_middleware(app):
    app = recording.appstats_wsgi_middleware(app)
    return app


#########################################
# Remote_API Authentication configuration.
#
# See google/appengine/ext/remote_api/handler.py for more information.
# For datastore_admin datastore copy, you should set the source appid
# value.  'HTTP_X_APPENGINE_INBOUND_APPID', ['trusted source appid here']
#
remoteapi_CUSTOM_ENVIRONMENT_AUTHENTICATION = (
    'HTTP_X_APPENGINE_INBOUND_APPID', ['ghidonations'])

# add `lib` subdirectory to `sys.path`, so our `main` module can load
# third-party libraries.
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'lib'))
