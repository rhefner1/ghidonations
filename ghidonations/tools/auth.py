import logging

import endpoints

from gaesessions import get_current_session
from ghidonations.db.individual import Individual
from ghidonations.tools.keys import get_user_key


def check_credentials(self, email, password):
    try:
        users = Individual.gql("WHERE email = :e", e=email)
        target_user = users.fetch(1)[0]

        if target_user.password == password:
            return True, target_user
        else:
            return False, None
    except Exception:
        return False, None


def check_authentication(self, admin_required, from_endpoints=False):
    try:
        # If the cookie doesn't exist, send them back to login
        u_key = get_user_key(self)
        u = u_key.get()

        # If the user tries to enter an admin page with standard credentials,
        # kick them out.
        if admin_required is True and u.admin is False:
            logging.info("Not authorized - kicking out")
            self.redirect("/ajax/notauthorized")

        # Otherwise, good to go
        return u.admin, u.settings.get()

    except Exception as e:
        message = "Error in checkAuthentication - kicking out to login page. " + str(e)
        logging.info(message)

        if from_endpoints:
            raise endpoints.ForbiddenException(message)
        else:
            self.redirect("/login")

        return None, None


def rpc_check_authentication(self, admin_required):
    try:
        self.session = get_current_session()

        # If the cookie doesn't exist, send them back to login
        if not self.session["key"]:
            return False
        else:
            # The cookie does exist, so store the key
            user_key = get_user_key(self)
            user = user_key.get()

            # Get admin privledges associated with this user
            user_privledges = user.admin

            # If the user tries to enter an admin page with standard credentials,
            # kick them out.
            if admin_required is True and user_privledges is False:
                return "semi"

            # Otherwise, good to go
            return True
    except Exception:
        return False
