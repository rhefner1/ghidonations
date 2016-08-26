import logging
import time

from ghidonations.data_tools.base import UtilitiesBase
from ghidonations.tools.util import convert_time, current_time
from google.appengine.api import mail, taskqueue, search
from google.appengine.ext.webapp import template

DONATION_SEARCH_INDEX = "donation"


class DonationAssign(UtilitiesBase):
    def associate_individual(self, individual_key, writeback):
        if self.e.individual != individual_key:
            # Just to make sure the association is actually changed - instead of marking the same value as it was before
            try:
                message = "Donation " + self.e.websafe + " associated with individual " + str(
                    individual_key.urlsafe()) + "."
                logging.info(message)
            except Exception:
                pass

            self.e.individual = individual_key

        if writeback is True:
            self.e.put()

    def associate_team(self, team_key, writeback):
        if self.e.team != team_key:
            # Just to make sure the association is actually changed - instead of marking the same value as it was before
            try:
                message = "Donation " + self.e.websafe + " associated with team " + str(team_key.urlsafe()) + "."
                logging.info(message)
            except Exception:
                pass

            self.e.team = team_key

        if writeback is True:
            self.e.put()

    def disassociate_individual(self, writeback):
        if self.e.individual:
            # Just to make sure the association is actually changed - instead of marking the same value as it was before
            message = "Donation " + self.e.websafe + " removed from individual " + str(
                self.e.individual.urlsafe()) + "."
            logging.info(message)

            self.e.individual = None

        if writeback is True:
            self.e.put()

    def disassociate_team(self, writeback):
        if self.e.team:
            # Just to make sure the association is actually changed - instead of marking the same value as it was before
            message = "Donation " + self.e.websafe + " removed from team `" + str(self.e.team.urlsafe()) + "."
            logging.info(message)

            self.e.team = None

        if writeback is True:
            self.e.put()


class DonationConfirmation(UtilitiesBase):
    def email(self):
        d = self.e

        if d.email or d.email != ['']:

            message = mail.EmailMessage()
            if d.given_email:
                # Email address that came from PayPal
                message.to = d.given_email
            else:
                # Email address associated with contact
                message.to = d.email[0]

            # TODO - is there any other way to get an organization's email address to appear if it's not verified?
            settings_name = d.settings.get().name
            if settings_name == "GHI":
                message.sender = "donate@globalhopeindia.org"
                message.subject = "Thanks for your donation!"
            else:
                message.sender = settings_name + " <mailer@ghidonations.appspotmail.com>"
                message.subject = settings_name + " - Thanks for your donation!"

            date = convert_time(d.donation_date).strftime("%B %d, %Y")
            s = d.settings.get()

            if d.individual:
                individual_name = d.individual.get().name
            elif d.team:
                individual_name = d.team.get().name
            else:
                individual_name = None

            template_variables = {"s": s, "d": d, "date": date, "individual_name": individual_name}

            who = "http://ghidonations.appspot.com"

            template_variables["see_url"] = d.confirmation.see_url(who)
            template_variables["print_url"] = d.confirmation.print_url(who)

            # Message body/HTML here
            message.html = template.render("pages/letters/thanks_email.html", template_variables)

            logging.info("Sending confirmation email to: " + d.email[0])

            # Adding to history
            logging.info("Confirmation email sent at " + current_time())

            message.send()

        else:
            logging.info("No email address to send confirmation.  Not continuing.")

    def print_url(self, who):
        if not who:
            who = ""

        return who + "/thanks?m=p&id=" + self.e.websafe

    def see_url(self, who):
        if not who:
            who = ""

        return who + "/thanks?m=w&id=" + self.e.websafe

    def task(self, countdown_secs):
        logging.info("Tasking confirmation email.  Delaying for " + str(countdown_secs) + " seconds.")
        taskqueue.add(url="/tasks/confirmation", params={'donation_key': self.e.websafe}, countdown=int(countdown_secs))


class DonationReview(UtilitiesBase):
    def archive(self):
        self.e.reviewed = True
        self.e.put()

    def mark_unreviewed(self):
        self.e.reviewed = False
        self.e.put()


class DonationSearch(UtilitiesBase):
    def create_document(self):
        d = self.e
        c = d.contact.get()
        email = d.email[0]
        if not email:
            email = ""

        reviewed = "no"
        if d.reviewed is True:
            reviewed = "yes"

        team_key = ""
        if d.team:
            team_key = d.team.urlsafe()

        individual_key = ""
        if d.individual:
            individual_key = d.individual.urlsafe()

        time_seconds = int(time.mktime(d.donation_date.timetuple()))

        document = search.Document(doc_id=d.websafe,
                                   fields=[
                                       search.TextField(name='donation_key', value=d.websafe),

                                       search.DateField(name='time', value=d.donation_date),
                                       search.TextField(name='name', value=c.name),
                                       search.TextField(name='email', value=email),
                                       search.NumberField(name='amount', value=float(d.amount_donated)),
                                       search.TextField(name='type', value=d.payment_type),

                                       search.TextField(name='team', value=d.designated_team),
                                       search.TextField(name='individual', value=d.designated_individual),

                                       search.TextField(name='reviewed', value=reviewed),

                                       search.TextField(name='formatted_donation_date',
                                                        value=d.formatted_donation_date),

                                       search.TextField(name='contact_key', value=d.contact.urlsafe()),
                                       search.TextField(name='team_key', value=team_key),
                                       search.TextField(name='individual_key', value=individual_key),
                                       search.TextField(name='settings', value=d.settings.urlsafe()),
                                       search.NumberField(name='timesort', value=time_seconds),
                                   ])

        return document

    def index(self):
        # Updates search index of this entity or creates new one if it doesn't exist
        index = search.Index(name=DONATION_SEARCH_INDEX)

        # Creating the new index
        try:
            doc = self.create_document()
            index.put(doc)

        except Exception as e:
            logging.error("Failed creating index on donation key:" + self.e.websafe + " because: " + str(e))
            self.error(500)
