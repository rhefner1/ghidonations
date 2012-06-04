import logging

#App engine platform
import wsgiref.handlers
import webapp2 as webapp

import GlobalUtilities as utilities

class NotFound(webapp.RequestHandler):
    def get(self, address):
        logging.info("404 error on address: " + str(address))
        utilities.giveError(self, 404)

app = webapp.WSGIApplication([
        (r'/(.*)', NotFound)],
        debug=True)
wsgiref.handlers.CGIHandler().run(app)