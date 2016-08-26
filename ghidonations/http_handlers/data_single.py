import ghidonations.tools.keys
from ghidonations.http_handlers.base import BaseHandlerAdmin
from ghidonations.tools import util
from google.appengine.ext.webapp import template


class Contact(BaseHandlerAdmin):
    def task(self, is_admin, s):
        contact_key = self.request.get("c")
        c = ghidonations.tools.keys.get_key(contact_key).get()

        template_variables = {"c": c, "s": s}
        self.response.write(
            template.render('pages/contact.html', template_variables))


class Deposit(BaseHandlerAdmin):
    def task(self, is_admin, s):

        # WARNING - this is a complicated and hacked-together solution.
        # I didn't understand it the day after I wrote it.
        # ... But it works.

        deposit_key = self.request.get("d")
        deposit = ghidonations.tools.keys.get_key(deposit_key).get()

        entity_keys = deposit.entity_keys
        gross_amount = util.to_decimal(0)
        net_amount = util.to_decimal(0)
        general_fund = util.to_decimal(0)

        donations = []
        team_breakout = {}

        for k in entity_keys:
            d = k.get()
            if d:
                donations.append(d)

                gross_amount += d.confirmation_amount
                net_amount += d.amount_donated

                if d.team:
                    t = d.team.get()
                    try:
                        team_breakout[t.name]
                    except Exception:
                        team_breakout[t.name] = [util.to_decimal(0), []]

                    team_breakout[t.name][0] += d.amount_donated

                    if d.individual:
                        i = d.individual.get()
                        array = [i.name, d.amount_donated]

                        team_breakout[t.name][1].append(array)
                else:
                    # Add count to general fund
                    general_fund += d.amount_donated

        team_breakout["General Fund"] = [util.to_decimal(general_fund), []]

        new_team_breakout = {}
        for k, v in team_breakout.items():
            name = k
            amount_donated = v[0]
            array = v[1]
            new_array = []

            for a in array:
                string = a[0] + " ($" + str(a[1]) + ")"
                new_array.append(string)

            new_team_breakout[unicode(name) + " ($" + str(amount_donated) + ")"] = new_array

        template_variables = {"d": deposit, "donations": donations, "team_breakout": new_team_breakout,
                              "gross_amount": gross_amount, "net_amount": net_amount}
        self.response.write(
            template.render('pages/deposit.html', template_variables))


class Settings(BaseHandlerAdmin):
    def task(self, is_admin, s):
        template_variables = {"s": s}
        self.response.write(
            template.render('pages/settings.html', template_variables))