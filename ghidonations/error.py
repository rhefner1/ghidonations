import logging
import wsgiref.handlers

import webapp2

from ghidonations.tools import util


class NotFound(webapp2.RequestHandler):
    def get(self, address):
        logging.info("404 error on address: " + str(address))
        util.give_error(self, 404)


app = webapp2.WSGIApplication([
    (r'/(.*)', NotFound)],
    debug=True)
wsgiref.handlers.CGIHandler().run(app)
