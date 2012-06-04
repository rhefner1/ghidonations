from gaesessions import SessionMiddleware
from google.appengine.ext.appstats import recording

# suggestion: generate your own random key using os.urandom(64)
# WARNING: Make sure you run os.urandom(64) OFFLINE and copy/paste the output to
# this file.  If you use os.urandom() to *dynamically* generate your key at
# runtime then any existing sessions will become junk every time you start,
# deploy, or update your app!
import os
COOKIE_KEY = '\x85R\xe2!P\xb9\x19<X\x00\xf4\x8a%\xe1\xc2-\x06\xc9@\xec\x84\xda\xb0v\x94i"y\xd0\xf0\xff\xc1\xf3\xd08p\xa8\xf7\xa1\x84h~\x85\xffX\x1d\x96l\x1e\tD\x82\t\xb5/a\xaf\xa8\xb3\xd8Il\xad\xcc'

def webapp_add_wsgi_middleware(app):
	app = SessionMiddleware(app, cookie_key=COOKIE_KEY)
	return app

def recording_add_wsgi_middleware(app):
 	app = recording.appstats_wsgi_middleware(app)
	return app
