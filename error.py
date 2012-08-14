#App engine platform
import webapp2, wsgiref.handlers, logging

import GlobalUtilities as utilities

class NotFound(webapp2.RequestHandler):
    def get(self, address):
        logging.info("404 error on address: " + str(address))
        utilities.giveError(self, 404)

app = webapp.WSGIApplication([
        (r'/(.*)', NotFound)],
        debug=True)
wsgiref.handlers.CGIHandler().run(app)