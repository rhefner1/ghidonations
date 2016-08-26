import json

from ghidonations import tools
from google.appengine.ext import ndb


class Settings(ndb.Expando):
    name = ndb.StringProperty()
    email = ndb.StringProperty()

    # Mailchimp values
    mc_use = ndb.BooleanProperty()
    mc_apikey = ndb.StringProperty()
    mc_donorlist = ndb.StringProperty()

    # Impressions
    impressions = ndb.StringProperty(repeated=True)

    # PayPal
    paypal_id = ndb.StringProperty()

    # Donate page
    amount1 = ndb.IntegerProperty()
    amount2 = ndb.IntegerProperty()
    amount3 = ndb.IntegerProperty()
    amount4 = ndb.IntegerProperty()
    use_custom = ndb.BooleanProperty()

    donate_parent = ndb.StringProperty()

    # Confirmation letters
    confirmation_text = ndb.TextProperty()
    confirmation_info = ndb.TextProperty()
    confirmation_header = ndb.TextProperty()
    confirmation_footer = ndb.TextProperty()
    donor_report_text = ndb.TextProperty()

    # Contact JSON
    contacts_json = ndb.TextProperty()

    # Analytics
    one_week_history = ndb.TextProperty()
    one_month_history = ndb.TextProperty()

    # Sets creation date
    creation_date = ndb.DateTimeProperty(auto_now_add=True)

    @property
    def create(self):
        return tools.SettingsCreate(self)

    @property
    def data(self):
        return tools.SettingsData(self)

    @property
    def exists(self):
        return tools.SettingsExists(self)

    @property
    def deposits(self):
        return tools.SettingsDeposits(self)

    @property
    def impressions_json(self):
        return json.dumps(self.impressions)

    @property
    def mailchimp(self):
        return tools.SettingsMailchimp(self)

    @property
    def refresh(self):
        return tools.SettingsRefresh(self)

    @property
    def search(self):
        return tools.SettingsSearch(self)

    def update(self, name, email, mc_use, mc_apikey, mc_donorlist, paypal_id, impressions, donate_parent, amount1,
               amount2, amount3, amount4, use_custom, confirmation_header, confirmation_info, confirmation_footer,
               confirmation_text, donor_report_text):
        s = self

        if name != s.name:
            s.name = name

        if email != s.email:
            s.email = email

            if email in tools.getAccountEmails():
                raise Exception("Cannot have the same email as another organization.")

        if mc_use != s.mc_use:
            s.mc_use = mc_use

        if mc_apikey != s.mc_apikey:
            s.mc_apikey = mc_apikey

        if mc_donorlist != s.mc_donorlist:
            s.mc_donorlist = mc_donorlist

        if paypal_id != s.paypal_id:
            s.paypal_id = paypal_id

        if impressions != s.impressions:
            s.impressions = impressions

        if donate_parent != s.donate_parent:
            s.donate_parent = donate_parent

        if int(amount1) != s.amount1:
            s.amount1 = int(amount1)

        if int(amount2) != s.amount2:
            s.amount2 = int(amount2)

        if int(amount3) != s.amount3:
            s.amount3 = int(amount3)

        if int(amount4) != s.amount4:
            s.amount4 = int(amount4)

        if use_custom != s.use_custom:
            s.use_custom = use_custom

        if confirmation_header != s.confirmation_header:
            s.confirmation_header = confirmation_header

        if confirmation_info != s.confirmation_info:
            s.confirmation_info = confirmation_info

        if confirmation_footer != s.confirmation_footer:
            s.confirmation_footer = confirmation_footer

        if confirmation_text != s.confirmation_text:
            s.confirmation_text = confirmation_text

        if donor_report_text != s.donor_report_text:
            s.donor_report_text = donor_report_text

        s.put()

    @property
    def websafe(self):
        return self.key.urlsafe()
