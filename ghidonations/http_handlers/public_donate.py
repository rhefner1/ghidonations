import webapp2

from ghidonations.tools import util
from google.appengine.ext.webapp import template


class DonatePage(webapp2.RequestHandler):
    def get(self):
        self.response.headers['Access-Control-Allow-Origin'] = '*'

        settings = self.request.get("s")

        try:
            s = util.get_key(settings).get()

            template_variables = {"s": s}
            self.response.write(
                template.render('pages/public_pages/pub_donate.html', template_variables))

        except Exception:
            self.response.write("Sorry, this URL triggered an error.  Please try again.")