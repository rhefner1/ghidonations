from ghidonations import tools
from ghidonations.tools.util import DecimalProperty
from google.appengine.ext import ndb


class TeamList(ndb.Model):
    individual = ndb.KeyProperty()
    team = ndb.KeyProperty()
    fundraise_amt = DecimalProperty()

    show_donation_page = ndb.BooleanProperty(default=True)
    show_progress_bar = ndb.BooleanProperty(default=True)

    sort_name = ndb.StringProperty()

    @property
    def data(self):
        return tools.TeamListData(self)

    @property
    def individual_name(self):
        return self.individual.get().name

    @property
    def team_name(self):
        return self.team.get().name

    @property
    def websafe(self):
        return self.key.urlsafe()
