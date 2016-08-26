import logging

from ghidonations.db.settings import Settings
from mailsnake import MailSnake


def get_account_emails():
    all_settings = Settings.query()
    all_emails = {}

    for s in all_settings:
        all_emails[s.email] = str(s.websafe)

    return all_emails


def get_mailchimp_lists(self, mc_apikey):
    ms = MailSnake(mc_apikey)
    response = ms.lists()

    try:
        mc_lists = {}

        for l in response["data"]:
            list_name = l["name"]
            mc_lists[list_name] = l["id"]

        return [True, mc_lists]
    except Exception:
        if response["code"] == 104:
            return [False, "Sorry, you entered an incorrect Mailchimp API Key"]
        else:
            return [False, "Unknown error"]


def new_settings(name, email):
    new_s = Settings()
    new_s.name = name
    new_s.email = email

    new_s.mc_use = False

    new_s.impressions = []

    new_s.amount1 = 10
    new_s.amount2 = 25
    new_s.amount3 = 75
    new_s.amount4 = 100
    new_s.use_custom = True

    logging.info("Settings created.")

    new_s.put()

    return new_s.key
