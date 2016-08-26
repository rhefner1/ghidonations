import json
import logging

from ghidonations import tools
from ghidonations.db.team_list import TeamList
from ghidonations.tools import util
from google.appengine.api import mail, memcache, taskqueue
from google.appengine.api import search
from google.appengine.ext import ndb, blobstore, deferred

_INDIVIDUAL_SEARCH_INDEX = "individual"


class Individual(ndb.Expando):
    name = ndb.StringProperty()
    email = ndb.StringProperty()

    # Determines which account this person belongs to
    settings = ndb.KeyProperty()

    # Credentials
    admin = ndb.BooleanProperty()
    password = ndb.StringProperty()

    # Profile
    description = ndb.TextProperty()
    photo = ndb.StringProperty()

    show_donation_page = ndb.BooleanProperty(default=True)
    show_progress_bar = ndb.BooleanProperty(default=True)

    # Sets creation date
    creation_date = ndb.DateTimeProperty(auto_now_add=True)

    @property
    def data(self):
        return tools.IndividualData(self)

    @property
    def teamlist_entities(self):
        q = TeamList.gql("WHERE individual = :i", i=self.key)
        return tools.qCache(q)

    @property
    def search(self):
        return tools.IndividualSearch(self)

    @property
    def websafe(self):
        return self.key.urlsafe()

    def email_user(self, msg_id):
        # Gives the user an email when something happens in their account
        if msg_id == 1:
            email_subject = "Recurring donation"
            email_message = "A new recurring donation was sent to you!"
        else:
            logging.debug("Called email_user with invalid message ID: '%s'" % msg_id)
            return

        message = mail.EmailMessage()
        message.sender = "donate@globalhopeindia.org"
        message.subject = email_subject
        message.to = self.email

        # Message body here - determined from msg_id
        message.body = email_message

        logging.info("Sending alert email to: " + self.email)

        # Adding to history
        logging.info("Alert email sent at " + tools.currentTime())

        message.send()

    def update(self, name, email, team_list, description, change_image, password, show_donation_page,
               show_progress_bar):
        name_changed = False
        show_donation_changed = False

        if name != self.name:
            self.name = name
            name_changed = True

        if email:
            if email != self.email:
                self.email = email

            if password and password != "" and self.password != password:
                self.password = password

        else:
            self.email = None
            self.password = None

        if show_donation_page != self.show_donation_page:
            self.show_donation_page = show_donation_page
            show_donation_changed = True

        if show_progress_bar != self.show_progress_bar:
            self.show_progress_bar = show_progress_bar
            show_donation_changed = True

        # Initializes DictDiffer object to tell differences from current dictionary to server-side one
        team = json.loads(team_list)
        dd = tools.DictDiffer(team, self.data.team_list)

        for key in dd.added():
            new_tl = TeamList()
            new_tl.individual = self.key
            new_tl.team = tools.getKey(key)
            new_tl.fundraise_amt = tools.toDecimal(team[key][1])

            new_tl.put()

        for key in dd.removed():
            query = TeamList.gql("WHERE team = :t AND individual = :i", t=tools.getKey(key), i=self.key)
            tl = query.fetch(1)[0]

            for d in tl.data.donations:
                d.team = None
                d.put()

            tl.key.delete()

        for key in dd.changed():
            query = TeamList.gql("WHERE team = :t AND individual = :i", t=tools.getKey(key), i=self.key)

            tl = query.fetch(1)[0]
            tl.fundraise_amt = tools.toDecimal(team[key][1])
            tl.put()

        if description != str(self.description):
            self.description = description

        if not change_image:
            # If change_image = None, there isn't any change. If it isn't, it
            # contains a
            if self.photo:
                # Delete old blob to keep it from orphaning
                old_blobkey = self.photo
                old_blob = blobstore.BlobInfo.get(old_blobkey)
                old_blob.delete()

            self.photo = change_image

        try:
            if name_changed or show_donation_changed:
                for tl in self.teamlist_entities:

                    if name_changed:
                        tl.sort_name = name

                    if show_donation_changed:
                        tl.show_donation_page = show_donation_page
                        tl.show_progress_bar = show_progress_bar

                    tl.put()
        except Exception:
            pass

        self.put()

        if name_changed:
            # Reindexing donations on name change
            taskqueue.add(url="/tasks/reindex", params={'mode': 'team', 'key': self.websafe}, countdown=1,
                          queue_name="backend")

    @classmethod
    def _post_put_hook(cls, future):
        e = future.get_result().get()

        deferred.defer(util.clear_team_memcache, e, _countdown=2, _queue="backend")

        taskqueue.add(url="/tasks/delayindexing", params={'e': e.websafe}, countdown=2, queue_name="delayindexing")

    @classmethod
    def _pre_delete_hook(cls, key):
        i = key.get()

        # Removing this individual's association with donations
        for d in i.data.donations:
            d.team = None
            d.individual = None
            d.put()

        for tl in i.data.teams:
            memcache.delete("teammembers" + tl.team.urlsafe())
            memcache.delete("publicteammembers" + tl.team.urlsafe())
            memcache.delete("teammembersdict" + tl.team.urlsafe())

            tl.key.delete()

        # Delete search index
        index = search.Index(name=_INDIVIDUAL_SEARCH_INDEX)
        index.delete(i.websafe)
