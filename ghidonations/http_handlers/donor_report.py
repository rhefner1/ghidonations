import ghidonations.tools.keys
from ghidonations.http_handlers.base import BaseHandlerAdmin
from ghidonations.tools import util
from google.appengine.ext.webapp import template


class DonorReport(BaseHandlerAdmin):
    def task(self, is_admin, s):
        try:

            contact_key = self.request.get("c")
            year = int(self.request.get("y"))

            if contact_key == "" or year == "" or len(str(year)) != 4:
                # Throw an error if you don't have those two pieces of info or if the year isn't a number
                raise Exception("Don't know contact key or year.")

            c = ghidonations.tools.keys.get_key(contact_key).get()
            s = c.settings.get()

            donations = c.data.annual_donations(year)
            donation_total = util.to_decimal(0)

            for d in donations:
                donation_total += d.confirmation_amount

            donation_total = "${:,.2f}".format(donation_total)

            template_variables = {"s": s, "c": c, "donations": donations, "year": str(year),
                                  "donation_total": str(donation_total), "street": c.address[0], "city": c.address[1],
                                  "state": c.address[2], "zip": c.address[3]}

            self.response.write(
                template.render("pages/letters/donor_report_print.html", template_variables))


        except Exception:
            # If there's a malformed URL, give a 500 error
            self.error(500)
            self.response.write(
                template.render('pages/letters/thankyou_error.html', {}))


class DonorReportSelect(BaseHandlerAdmin):
    def task(self, is_admin, s):
        template_variables = {"s": s}
        self.response.write(
            template.render('pages/donor_report_select.html', template_variables))