import GlobalUtilities as tools
from gaesessions import SessionMiddleware
from google.appengine.api import memcache
from google.appengine.ext.appstats import recording

# suggestion: generate your own random key using os.urandom(64)
# WARNING: Make sure you run os.urandom(64) OFFLINE and copy/paste the output to
# this file.  If you use os.urandom() to *dynamically* generate your key at
# runtime then any existing sessions will become junk every time you start,
# deploy, or update your app!

COOKIE_KEY = memcache.get("COOKIE_KEY")
GCS_BUCKET = memcache.get("GCS_BUCKET")

if not COOKIE_KEY or not GCS_BUCKET:
    global_settings = tools.getGlobalSettings()

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
