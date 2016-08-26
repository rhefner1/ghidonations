from gaesessions import get_current_session
from google.appengine.ext import ndb


def get_username(self):
    try:
        user_key = get_user_key(self)
        user = user_key.get()

        return user.name
    except Exception:
        self.redirect("/login")


def get_user_key(self):
    self.session = get_current_session()
    user_key = self.session["key"]

    if not user_key:
        raise Exception("User key is none")

    return get_key(user_key)


def get_settings_key(self, endpoints=False):
    try:
        user_key = get_user_key(self)
        user = user_key.get()

        return user.settings

    except Exception:
        if endpoints:
            raise Exception("Error in getSettingsKey")
        else:
            self.redirect("/login")


def get_key(entity_key):
    return ndb.Key(urlsafe=entity_key)


def get_key_if_exists(websafe_key):
    try:
        key = get_key(websafe_key)
        key.get()

        # If exception hasn't been thrown, the key exists
        return key
    except Exception:
        return None