import ghidonations.tools.keys
from ghidonations.http_handlers.base import BaseHandlerAdmin
from ghidonations.tools import auth
from google.appengine.ext.webapp import template


class NewContact(BaseHandlerAdmin):
    def task(self, is_admin, s):
        template_variables = {}
        self.response.write(
            template.render('pages/new_contact.html', template_variables))


class NewIndividual(BaseHandlerAdmin):
    def task(self, is_admin, s):
        template_variables = {"teams": s.data.all_teams}
        self.response.write(
            template.render('pages/new_individual.html', template_variables))


class NewTeam(BaseHandlerAdmin):
    def task(self, is_admin, s):
        template_variables = {}
        self.response.write(
            template.render('pages/new_team.html', template_variables))


class OfflineDonation(BaseHandlerAdmin):
    def task(self, is_admin, s):
        i = ghidonations.tools.keys.get_user_key(self).get()

        template_variables = {"individual_name": i.name, "individual_key": i.key.urlsafe(), "teams": s.data.all_teams}

        self.response.write(
            template.render('pages/offline.html', template_variables))