import webapp2

import ghidonations.tools.keys
from ghidonations.http_handlers.base import BaseHandlerAdmin
from ghidonations.tools import util
from google.appengine.ext.webapp import template


class IndividualWelcome(BaseHandlerAdmin):
    def task(self, is_admin, s):
        try:
            mode = self.request.get("m")
            individual_key = self.request.get("i")

            if mode == "" or individual_key == "":
                # Throw an error if you don't have those two pieces of info
                raise Exception("Don't know mode or individual_key.")

            i = ghidonations.tools.keys.get_key(individual_key).get()
            s = ghidonations.tools.keys.get_key(i.settings).get()

            template_variables = {"s": s, "i": i}
            self.response.write(
                template.render('pages/letters/individual.html', template_variables))

        except Exception:
            # If there's a malformed URL, give a 500 error
            self.error(500)
            self.response.write(
                template.render('pages/letters/thankyou_error.html', {}))


class ThankYou(webapp2.RequestHandler):
    def get(self):
        try:
            mode = self.request.get("m")
            donation_key = self.request.get("id")

            if mode == "" or donation_key == "":
                # Throw an error if you don't have those two pieces of info
                raise Exception("Don't know mode or donation key.")

            d = ghidonations.tools.keys.get_key(donation_key).get()
            date = util.convert_time(d.donation_date).strftime("%B %d, %Y")
            s = d.settings.get()

            if d.individual:
                individual_name = d.individual.get().name
            elif d.team:
                individual_name = d.team.get().name
            else:
                individual_name = None

            template_variables = {"s": s, "d": d, "c": d.contact, "date": date, "individual_name": individual_name}

            if mode == "w":
                template_location = "pages/letters/thanks_live.html"

            elif mode == "p":
                template_location = "pages/letters/thanks_print.html"

            elif mode == "e":
                who = "http://ghidonations.appspot.com"

                template_variables["see_url"] = d.confirmation.see_url(who)
                template_variables["print_url"] = d.confirmation.print_url(who)

                template_location = "pages/letters/thanks_email.html"

            else:
                raise ValueError("Invalid mode '%s'. Cannot continue." % mode)

            self.response.write(
                template.render(template_location, template_variables))

        except Exception:
            # If there's a malformed URL, give a 500 error
            self.error(500)
            self.response.write(
                template.render('pages/letters/thankyou_error.html', {}))