from gaesessions import SessionMiddleware
from google.appengine.ext.appstats import recording

# suggestion: generate your own random key using os.urandom(64)
# WARNING: Make sure you run os.urandom(64) OFFLINE and copy/paste the output to
# this file.  If you use os.urandom() to *dynamically* generate your key at
# runtime then any existing sessions will become junk every time you start,
# deploy, or update your app!

COOKIE_KEY = '\xdaQ\x14\x9f\x86\xc4j\xe3\x02]\xf5\xdd\xd7\xfd\x0e\xfbiXij,\x87\xfc\xb3\xa6\xff\xa4\xf0\xcbdZ\xedE\xa4]\xd6\xd4\x8f\x1b\xb3\xf6Ty6\xa8\xd2\x11kQ\xc3\xd4\x0b\xdf+\x8e\xe4`3g1\x1b\xe6\xad\x17'
GOOGLE_API_KEY = ""

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
