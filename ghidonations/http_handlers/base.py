import logging

import webapp2

from gaesessions import get_current_session
from ghidonations.tools import auth
from google.appengine.ext.webapp import template


class BaseHandler(webapp2.RequestHandler):
    def get(self):
        # By default, need admin privileges to view
        is_admin, s = auth.check_authentication(self, False)

        if is_admin is None and s is None:
            self.redirect("/login")
        else:
            return self.task(is_admin, s)

    def task(self, is_admin, s):
        self.response.out.write("BaseHandler default response out.")


class BaseHandlerAdmin(webapp2.RequestHandler):
    def get(self):
        # By default, need admin privileges to view
        is_admin, s = auth.check_authentication(self, True)

        if is_admin is None and s is None:
            self.redirect("/login")
        else:
            return self.task(is_admin, s)

    def task(self, is_admin, s):
        self.response.out.write("BaseHandlerAdmin default response out.")


class Container(BaseHandler):
    def task(self, is_admin, s):
        username = auth.get_username(self)
        logging.info("Loading container for: " + str(username))

        session = get_current_session()

        redirect = False
        mobile_redirect = "none"

        user_agent = str(self.request.headers['User-Agent'])
        mobile_devices = ["android", "blackberry", "googlebot-mobile", "iemobile", "iphone", "ipod", "opera", "mobile",
                          "palmos", "webos"]

        # If user agent matches anything in the list above, redirect
        for m in mobile_devices:
            if user_agent.lower().find(m) != -1:
                redirect = True

        # If user has explicitly requested to be sent to desktop site
        try:
            if session["no-redirect"] == "1":
                redirect = False
                mobile_redirect = "block"
        except Exception:
            pass

        if redirect:
            self.redirect("/m")
            return

        try:
            template_variables = {"settings": s.key.urlsafe(), "username": username, "mobile_redirect": mobile_redirect}
        except Exception:
            self.redirect("/login")
            return

        if is_admin is True:
            self.response.write(
                template.render('pages/container.html', template_variables))

        elif is_admin is False:
            self.response.write(
                template.render('pages/container_ind.html', template_variables))