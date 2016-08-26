import logging

from ghidonations import tools
from google.appengine.api import memcache, taskqueue
from google.appengine.api import search
from google.appengine.ext import ndb

_TEAM_SEARCH_INDEX = "team"


class Team(ndb.Expando):
    name = ndb.StringProperty()
    settings = ndb.KeyProperty()
    show_team = ndb.BooleanProperty()

    # Sets creation date
    creation_date = ndb.DateTimeProperty(auto_now_add=True)

    @property
    def data(self):
        return tools.TeamData(self)

    @property
    def search(self):
        return tools.TeamSearch(self)

    @property
    def websafe(self):
        return self.key.urlsafe()

    def update(self, name, show_team):
        name_changed = False

        if name != self.name:
            self.name = name
            name_changed = True

        if show_team != self.show_team:
            self.show_team = show_team

        self.put()

        if name_changed:
            # Reindexing donations on name change
            taskqueue.add(url="/tasks/reindex", params={'mode': 'team', 'key': self.websafe}, countdown=1,
                          queue_name="backend")

    @classmethod
    def _post_put_hook(cls, future):
        e = future.get_result().get()
        memcache.delete('allteams' + e.settings.urlsafe())
        memcache.delete("teammembers" + e.websafe)
        memcache.delete("publicteammembers" + e.websafe)
        memcache.delete("teamsdict" + e.settings.urlsafe())

        taskqueue.add(url="/tasks/delayindexing", params={'e': e.websafe}, countdown=2, queue_name="delayindexing")

    @classmethod
    def _pre_delete_hook(cls, key):
        t = key.get()
        logging.info("Deleting team:" + t.name)

        for tl in t.data.members:
            if tl:
                # Delete this team from all
                tl.key.delete()

        for d in t.data.donations:
            d.individual = None
            d.team = None
            d.put()

        # Delete search index
        index = search.Index(name=_TEAM_SEARCH_INDEX)
        index.delete(t.websafe)
