from ghidonations.http_handlers.base import BaseHandlerAdmin
from google.appengine.ext.webapp import template


class MergeContacts(BaseHandlerAdmin):
    def task(self, is_admin, s):
        template_variables = {}
        self.response.write(
            template.render('pages/merge_contacts.html', template_variables))