import json

from ghidonations.http_handlers.base import BaseHandlerAdmin, BaseHandler
from ghidonations.tools import util, auth
from google.appengine.ext.webapp import template


class ReviewQueue(BaseHandlerAdmin):
    def task(self, is_admin, s):
        search_query = self.request.get("search")

        template_variables = {"search_query": search_query}
        self.response.write(
            template.render('pages/review_queue.html', template_variables))


class ReviewQueueDetails(BaseHandler):
    def task(self, is_admin, s):
        donation_key = self.request.get("id")
        if donation_key == "":
            # If they didn't type any arguments into the address bar - meaning it didn't come from the app
            util.give_error(self, 500)
        else:
            # Getting donation by its key (from address bar argument)
            d = util.get_key(donation_key).get()

            i_key = auth.get_user_key(self)
            i = i_key.get()

            donation_date = [d.donation_date.day, d.donation_date.month, d.donation_date.year]
            donation_date = json.dumps(donation_date)

            template_variables = {"d": d, "s": s, "i": i, "donation_date": donation_date}
            self.response.write(
                template.render('pages/rq_details.html', template_variables))