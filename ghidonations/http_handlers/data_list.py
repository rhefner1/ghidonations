from ghidonations.http_handlers.base import BaseHandlerAdmin
from ghidonations.tools import util
from google.appengine.ext.webapp import template


class AllContacts(BaseHandlerAdmin):
    def task(self, is_admin, s):
        search_query = self.request.get("search")

        template_variables = {"search_query": search_query}
        self.response.write(
            template.render('pages/all_contacts.html', template_variables))


class AllDeposits(BaseHandlerAdmin):
    def task(self, is_admin, s):
        search_query = self.request.get("search")

        template_variables = {"search_query": search_query}
        self.response.write(
            template.render('pages/all_deposits.html', template_variables))


class AllIndividuals(BaseHandlerAdmin):
    def task(self, is_admin, s):
        search_query = self.request.get("search")

        template_variables = {"search_query": search_query}
        self.response.write(
            template.render('pages/all_individuals.html', template_variables))


class AllTeams(BaseHandlerAdmin):
    def task(self, is_admin, s):
        search_query = self.request.get("search")

        template_variables = {"search_query": search_query}
        self.response.write(
            template.render('pages/all_teams.html', template_variables))


class TeamMembers(BaseHandlerAdmin):
    def task(self, is_admin, s):
        team_key = self.request.get("t")
        t = util.get_key(team_key).get()

        template_variables = {"t": t}
        self.response.write(
            template.render('pages/team_members.html', template_variables))


class UndepositedDonations(BaseHandlerAdmin):
    def task(self, is_admin, s):
        template_variables = {"donations": s.data.undeposited_donations}
        self.response.write(
            template.render('pages/undeposited_donations.html', template_variables))