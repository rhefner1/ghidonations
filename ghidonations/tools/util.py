import datetime
from decimal import Decimal

import os
import re

from gaesessions import get_current_session
from ghidonations.db.global_settings import GlobalSettings
from ghidonations.tools.keys import get_key
from google.appengine.api import memcache
from google.appengine.api import search, datastore_errors
from google.appengine.datastore.datastore_query import Cursor
from google.appengine.ext import ndb
from google.appengine.ext.webapp import template


class DecimalProperty(ndb.StringProperty):
    def _validate(self, value):
        if not isinstance(value, (Decimal, str)):
            raise datastore_errors.BadValueError('Expected decimal or string, got %r' % (value,))

        return value

    def _to_base_type(self, value):
        return str(value)

    def _from_base_type(self, value):
        return to_decimal(value)


def clear_team_memcache(e):
    for t in e.data.teams:
        memcache.delete("teammembers" + t.team.urlsafe())
        memcache.delete("publicteammembers" + t.team.urlsafe())
        memcache.delete("teammembersdict" + t.team.urlsafe())
        memcache.delete("info" + t.team.urlsafe() + e.websafe)


def current_time():
    # Outputs current date and time
    return convert_time(datetime.datetime.utcnow()).strftime("%b %d, %Y %I:%M:%S %p")


def convert_time(orig_time):
    utc_zone = UTC()
    to_zone = EST()
    orig_time = orig_time.replace(tzinfo=utc_zone)

    return orig_time.astimezone(to_zone)


def get_websafe_cursor(cursor_object):
    if cursor_object:
        return cursor_object.web_safe_string
    else:
        return None


def get_flash(self):
    try:
        self.session = get_current_session()
        message = self.session["flash"]
        self.session["flash"] = ""
        if not message:
            message = ""
    except Exception:
        message = ""

    return message


def get_global_settings():
    q = GlobalSettings.query()

    try:
        global_settings = q.fetch(1)[0]

    except Exception:
        new_global_settings = GlobalSettings()
        new_global_settings.cookie_key = os.urandom(64).encode("base64")
        global_settings = new_global_settings.put()

        global_settings = global_settings.get()

    return global_settings


def get_search_doc(doc_id, index):
    if not doc_id:
        return None

    try:
        response = index.get_range(
            start_id=doc_id, limit=1, include_start_object=True)

        if response.results and response.results[0].doc_id == doc_id:
            return response.results[0]

        return None

    except search.InvalidRequest:  # catches ill-formed doc ids
        return None


def give_error(self, error_code):
    # checkAuthentication(self, False)

    self.error(error_code)
    self.response.write(
        template.render('pages/error.html', {}))


def gql_to_dict(self, gql_query):
    # Converts GQLQuery of App Engine data models to dictionary objects
    # An empty list to start out with - will be what we return
    all_objects = []

    for o in gql_query:
        new_dict = o.to_dict()
        new_dict["key"] = o.key.urlsafe()
        all_objects.append(new_dict)

    return all_objects


def is_email_address(email):
    if email:
        if re.match("^.+\\@(\\[?)[a-zA-Z0-9\\-\\.]+\\.([a-zA-Z]{2,3}|[0-9]{1,3})(\\]?)$", email):
            return True
        else:
            return False
    else:
        return False


def list_diff(list1, list2):
    # Typically old value is list1, new value is list2
    diff = list(set(list2) - set(list1))

    try:
        diff.remove('')
    except Exception:
        pass

    return diff


def money_amount(money_string):
    money = to_decimal(money_string)
    money = "${:,.2f}".format(money)
    return money


def ndb_key_to_urlsafe(keys):
    urlsafe_keys = []

    for k in keys:
        urlsafe_keys.append(k.urlsafe())

    return urlsafe_keys


def query_cursor_db(query, encoded_cursor, keys_only=False, num_results=_NUM_RESULTS):
    if encoded_cursor:
        query_cursor = Cursor.from_websafe_string(encoded_cursor)
        entities, cursor, more = query.fetch_page(num_results, start_cursor=query_cursor, keys_only=keys_only)
    else:
        entities, cursor, more = query.fetch_page(num_results, keys_only=keys_only)

    if more:
        new_cursor = cursor.to_websafe_string()
    else:
        new_cursor = None

    return [entities, new_cursor]


def set_flash(self, message):
    self.session = get_current_session()
    self.session["flash"] = message


def str_array_to_key(self, str_array):
    key_array = []
    for k in str_array:
        key_array.append(get_key(k))

    return key_array


def to_decimal(number):
    if number:
        # Stripping amount donated from commas, etc
        non_decimal = re.compile(r'[^\d.-]+')
        number = non_decimal.sub('', str(number))

        return Decimal(number).quantize(Decimal("1.00"))
    else:
        return Decimal(0).quantize(Decimal("1.00"))


def truncate_email(email, is_list=False):
    if is_list is True:
        new_email = ""
        for e in email:
            new_email += e + " "

        email = new_email

    truncation_length = 35
    if len(email) > truncation_length:
        email = email[0:truncation_length]
        email = email.replace(' ', ', ')
        email += "..."

    return email


class DictDiffer(object):
    """
    Calculate the difference between two dictionaries as:
    (1) items added
    (2) items removed
    (3) keys same in both but changed values
    (4) keys same in both and unchanged values
    """

    def __init__(self, current_dict, past_dict):
        self.current_dict, self.past_dict = current_dict, past_dict
        self.set_current, self.set_past = set(current_dict.keys()), set(past_dict.keys())
        self.intersect = self.set_current.intersection(self.set_past)

    def added(self):
        return self.set_current - self.intersect

    def removed(self):
        return self.set_past - self.intersect

    def changed(self):
        return set(o for o in self.intersect if self.past_dict[o] != self.current_dict[o])

    def unchanged(self):
        return set(o for o in self.intersect if self.past_dict[o] == self.current_dict[o])


class EST(datetime.tzinfo):
    def utcoffset(self, dt):
        return datetime.timedelta(hours=-4, minutes=0)

    def tzname(self, dt):
        return "GMT -4"

    def dst(self, dt):
        return datetime.timedelta(0)


class UTC(datetime.tzinfo):
    def utcoffset(self, dt):
        return datetime.timedelta(0)

    def tzname(self, dt):
        return "UTC"

    def dst(self, dt):
        return datetime.timedelta(0)
