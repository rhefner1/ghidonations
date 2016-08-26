import webapp2

import ghidonations.tools.keys
from gaesessions import get_current_session
from ghidonations.http_handlers.base import BaseHandler
from ghidonations.tools import auth
from google.appengine.ext.webapp import template


class Mobile(BaseHandler):
    def task(self, is_admin, s):
        i_key = ghidonations.tools.keys.get_user_key(self)
        i = i_key.get()

        template_variables = {"i": i}
        self.response.write(
            template.render('pages/mobile.html', template_variables))


class MobileRedirectSetting(webapp2.RequestHandler):
    def get(self):
        session = get_current_session()
        setting = self.request.get("r")

        session["no-redirect"] = setting

        self.redirect("/")