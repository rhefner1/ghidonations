import logging

import webapp2

from gaesessions import get_current_session
from ghidonations.tools import util, auth
from google.appengine.ext.webapp import template


class Login(webapp2.RequestHandler):
    def get(self):
        self.session = get_current_session()

        # Flash message
        message = util.get_flash(self)

        # Delete existing session if it exists
        self.session.terminate()

        template_variables = {"flash": message}
        self.response.write(
            template.render('pages/login.html', template_variables))

    def post(self):
        self.session = get_current_session()

        email = self.request.get("email")
        password = self.request.get("password")

        if email != "" and password != "":
            authenticated, user = auth.check_credentials(self, email, password)

        else:
            authenticated = False
            user = None

        if authenticated is True:
            logging.info("Authenticated: " + str(authenticated) + " and User: " + str(user.name))

            # Log in
            self.session["key"] = str(user.key.urlsafe())
            self.redirect("/")

        else:
            # Invalid login
            logging.info("Incorrect login.")
            util.set_flash(self, "Whoops, that didn't get you in. Try again.")
            self.redirect("/login")


class Logout(webapp2.RequestHandler):
    def get(self):
        self.session = get_current_session()
        self.session.terminate()

        self.redirect("/login")


class NotAuthorized(webapp2.RequestHandler):
    def get(self):
        template_variables = {}
        self.response.write(
            template.render('pages/not_authorized.html', template_variables))