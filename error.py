#App engine platform
import webapp2, wsgiref.handlers, logging

class NotFound(webapp2.RequestHandler):
    def get(self, address):
        logging.info("404 error on address: " + str(address))
        self.error(404)
        self.response.write(
                   template.render('pages/error.html', {}))

app = webapp2.WSGIApplication([
        (r'/(.*)', NotFound)],
        debug=True)