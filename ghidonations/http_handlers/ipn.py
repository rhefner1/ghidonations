import json
import logging
import urllib

import webapp2

from ghidonations.db.donation import Donation
from ghidonations.tools import data_access, util
from google.appengine.api import urlfetch


class IPN(webapp2.RequestHandler):
    def get(self):
        self.response.write("GHI Donations - PayPal IPN Handler")

    def post(self):
        # Below URL used for the live version.
        PP_URL = "https://www.paypal.com/cgi-bin/webscr"

        # Below URL used for testing with the sandbox - if this is uncommented, all real
        # donations will not be authenticated. ONLY use with dev versions.
        # PP_URL = "https://www.sandbox.paypal.com/cgi-bin/webscr"

        # Gets all account emails from Settings data models
        # to authenticate PayPal (don't accept payment from unknown)
        all_account_emails = data_access.get_account_emails()

        parameters = None
        if self.request.POST:
            parameters = self.request.POST.copy()
        if self.request.GET:
            parameters = self.request.GET.copy()

        payment_status = self.request.get("payment_status")
        logging.info("Payment status: " + payment_status)

        # Check payment is completed, not Pending or Failed.
        if payment_status == "Failed" or payment_status == "Pending":
            logging.error("Payment status is " + payment_status + ", so not continuing.")

        else:
            logging.info("All parameters: " + str(parameters))

            # Check the IPN POST request came from real PayPal, not from a fraudster.
            if parameters:
                parameters['cmd'] = '_notify-validate'

                # Encode the parameters in UTF-8 out of Unicode
                str_parameters = {}
                for k, v in parameters.iteritems():
                    str_parameters[k] = unicode(v).encode('utf-8')

                params = urllib.urlencode(str_parameters)
                status = urlfetch.fetch(
                    url=PP_URL,
                    method=urlfetch.POST,
                    payload=params,
                ).content
                if not status == "VERIFIED":
                    logging.debug("PayPal returned status:" + str(status))
                    logging.debug('Error. The request could not be verified, check for fraud.')
                    parameters['homemadeParameterValidity'] = False

            # Comparing receiver email to list of allowed email addresses
            try:
                receiver_email = parameters['receiver_email']

                # If the receiver_email isn't in the database, this will fail
                settings = all_account_emails[receiver_email]
                authenticated = True
                logging.info("Getting payment to account: " + receiver_email + ", #: " + settings)

            except Exception:
                settings = None
                authenticated = False
                logging.info("No match for incoming payment email address. Not continuing.")

            # Make sure money is going to the correct account - otherwise fraudulent
            if authenticated is True:
                # Currency of the donation
                # currency = parameters['mc_currency']

                s = util.get_key(settings).get()
                ipn_data = str(parameters)

                # Email and payer ID  numbers
                try:
                    email = parameters['payer_email']
                except Exception:
                    email = None

                try:
                    name = parameters['first_name'] + " " + parameters['last_name']
                except Exception:
                    name = "Anonymous Donor"

                # Check if an address was given by the donor
                try:
                    # Stich all the address stuff together
                    address = [parameters['address_street'], parameters['address_city'], parameters['address_state'],
                               parameters['address_zip']]

                except Exception:
                    address = None

                # Reading designation and notes values encoded in JSON from
                # donate form
                decoded_custom = None

                try:
                    decoded_custom = json.loads(parameters["custom"])

                    team_key = util.get_key_if_exists(decoded_custom[0])
                    individual_key = util.get_key_if_exists(decoded_custom[1])
                    special_notes = decoded_custom[2]

                    if s.exists.entity(team_key) is False:
                        team_key = None
                    if s.exists.entity(individual_key) is False:
                        individual_key = None

                except Exception:
                    logging.error("Excepted on designation.")
                    team_key = None
                    individual_key = None
                    special_notes = None

                try:
                    cover_trans = decoded_custom[3]
                    email_subscr = decoded_custom[4]
                except Exception:
                    cover_trans = False
                    email_subscr = False

                try:
                    phone = parameters['contact_phone']

                    if len(phone) > 10:
                        special_notes += "\nContact phone: " + phone
                        phone = None
                except Exception:
                    logging.info("Excepted on phone number.")
                    phone = None

                confirmation_amount = util.to_decimal(0)
                amount_donated = util.to_decimal(0)
                try:
                    confirmation_amount = parameters['mc_gross']
                    amount_donated = float(parameters['mc_gross']) - float(parameters['mc_fee'])

                except Exception:
                    pass

                # Find out what kind of payment this was - recurring, one-time, etc.
                try:
                    payment_type = parameters['txn_type']
                except Exception:
                    logging.info("Txn_type not available, so continuing with payment status")
                    payment_type = payment_status

                if payment_type == "recurring_payment_profile_created" or payment_type == "subscr_signup":
                    logging.info("This is the start of a recurring payment. Create info object.")

                    payment_id = parameters['subscr_id']

                    # Duration between payments
                    duration = "recurring"

                    # s.create.recurring_donation(payment_id, duration, ipn_data)

                elif payment_type == "recurring_payment" or payment_type == "subscr_payment":
                    logging.info("This is a recurring donation payment.")

                    payment_id = parameters['subscr_id']
                    payment_type = "recurring"

                    # Create a new donation
                    s.create.donation(name, email, amount_donated, payment_type,
                                      confirmation_amount=confirmation_amount,
                                      phone=phone, address=address, team_key=team_key, individual_key=individual_key,
                                      payment_id=payment_id, special_notes=special_notes, email_subscr=email_subscr,
                                      ipn_data=ipn_data)

                elif payment_type == "web_accept":
                    logging.info("This is a one-time donation.")

                    if payment_status == "Completed":
                        payment_id = parameters['txn_id']

                        # Create a new donation
                        s.create.donation(name, email, amount_donated, "one-time",
                                          confirmation_amount=confirmation_amount, address=address,
                                          team_key=team_key, individual_key=individual_key, payment_id=payment_id,
                                          special_notes=special_notes,
                                          email_subscr=email_subscr, ipn_data=ipn_data)

                    else:
                        logging.info("Payment status not complete.  Not logging the donation.")

                elif payment_type == "subscr_cancel":
                    logging.info("A subscriber has cancelled.")
                    amount_donated = "N/A"

                elif payment_type == "subscr_failed":
                    logging.info("A subscriber payment has failed.")
                    amount_donated = "N/A"

                elif payment_type == "Refunded":
                    try:
                        donation = Donation.gql("WHERE payment_id = :t", t=parameters["txn_id"])
                        donation_key = donation[0].key()

                        donation_key.delete()
                        logging.info("Refund detected and donation deleted. (" + donation_key.urlsafe() + ")")
                    except Exception:
                        logging.info("Donation tried to be deleted, but failed. Most likely already deleted.")

                try:
                    logging.info("Recording IPN")
                    logging.info("Payment type: " + payment_type)
                    logging.info("Name: " + name)
                    logging.info("Email: " + email)
                    logging.info("Amount donated: " + str(amount_donated))
                except Exception:
                    logging.error("Failed somewhere in the logs.")