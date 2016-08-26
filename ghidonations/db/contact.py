import json

from ghidonations import tools
from google.appengine.api import memcache, taskqueue
from google.appengine.api import search
from google.appengine.ext import ndb

_CONTACT_SEARCH_INDEX = "contact"


class Contact(ndb.Expando):
    name = ndb.StringProperty()
    email = ndb.StringProperty(repeated=True)
    phone = ndb.StringProperty()
    address = ndb.StringProperty(repeated=True)
    notes = ndb.TextProperty(indexed=True)

    settings = ndb.KeyProperty()

    # Sets creation date
    creation_date = ndb.DateTimeProperty(auto_now_add=True)

    @property
    def address_json(self):
        return json.dumps(self.address)

    @property
    def address_formatted(self):
        a = self.address
        if not a == ["", "", "", ""]:
            return a[0] + "\n" + a[1] + ", " + a[2] + "  " + a[3]
        else:
            return ""

    @property
    def create(self):
        return tools.ContactCreate(self)

    @property
    def data(self):
        return tools.ContactData(self)

    @property
    def search(self):
        return tools.ContactSearch(self)

    @property
    def websafe(self):
        return self.key.urlsafe()

    def update(self, name, email, phone, notes, address):
        settings = self.settings.get()

        # Changing blank values to None
        if name == "":
            name = None
        if not email:
            email = [""]

        if name != self.name and name:
            self.name = name
            name_changed = True

        else:
            name_changed = False

        if email != self.email:
            self.email = email

            if settings.mc_use:
                for e in email:
                    if e and e != "":
                        settings.mailchimp.add(e, name, False)

        if phone != self.phone:
            self.phone = phone

        if notes != str(self.notes):
            if not notes:
                notes = ""
            self.notes = notes

        if address != self.address:
            if address and address != "" and address != "None":
                # If the address is something and is different than that on file
                self.address = address

        # And now to put that contact back in the datastore
        self.put()

        if name_changed:
            # Reindexing donations on name change
            taskqueue.add(url="/tasks/reindex", params={'mode': 'contact', 'key': self.websafe}, countdown=1,
                          queue_name="backend")

    @classmethod
    def _post_put_hook(cls, future):
        e = future.get_result().get()
        memcache.delete("contacts%s" % e.settings.urlsafe())

        e.settings.get().refresh.contacts_json()
        taskqueue.add(url="/tasks/delayindexing", params={'e': e.websafe}, queue_name="delayindexing")

    @classmethod
    def _pre_delete_hook(cls, key):
        e = key.get()

        # Delete search index
        index = search.Index(name=_CONTACT_SEARCH_INDEX)
        index.delete(e.websafe)
