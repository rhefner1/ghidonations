from ghidonations.http_handlers.base import BaseHandlerAdmin
from google.appengine.ext.webapp import template


class Dashboard(BaseHandlerAdmin):
    def task(self, is_admin, s):
        vals = s.data.one_week_history

        past_donations = vals[0]
        past_money = str(vals[1])

        template_variables = {"num_open_donations": s.data.num_open_donations, "past_donations": past_donations,
                              "past_money": past_money}
        self.response.write(
            template.render('pages/dashboard.html', template_variables))