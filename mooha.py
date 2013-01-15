#App engine platform
import webapp2, appengine_config, logging, json, quopri, urllib
from datetime import datetime
from time import strftime

from google.appengine.ext.webapp import template, blobstore_handlers
from google.appengine.ext import blobstore
from google.appengine.api import urlfetch

#Excel export
from xlwt import *

#Sessions
from gaesessions import get_current_session

#Application files
import DataModels as models
import GlobalUtilities as tools

class BaseHandler(webapp2.RequestHandler):
    def get(self):
        #By default, need admin priveleges to view
        isAdmin, s = tools.checkAuthentication(self, False)

        if isAdmin == None and s == None:
            self.redirect("/login")
        else:
            return self.task(isAdmin, s)

    def task(self, isAdmin, s):
        self.response.out.write("BaseHandler default response out.")

class BaseHandlerAdmin(webapp2.RequestHandler):
    def get(self):
        #By default, need admin priveleges to view
        isAdmin, s = tools.checkAuthentication(self, True)

        if isAdmin == None and s == None:
            self.redirect("/login")
        else:
            return self.task(isAdmin, s)

    def task(self, isAdmin, s):
        self.response.out.write("BaseHandlerAdmin default response out.")

class AllContacts(BaseHandlerAdmin):
    def task(self, isAdmin, s):
        response = s.data.contacts(None)
        contacts = response[0]
        initial_cursor = response[1]

        template_variables = {"contacts" : contacts, "initial_cursor" : initial_cursor}
        self.response.write(
           template.render('pages/all_contacts.html', template_variables))

class AllDeposits(BaseHandlerAdmin):
    def task(self, isAdmin, s):
        response = s.data.deposits(None)
        deposits = response[0]
        initial_cursor = response[1]

        template_variables = {"deposits" : deposits, "initial_cursor" : initial_cursor}
        self.response.write(
                template.render('pages/all_deposits.html', template_variables))

class AllIndividuals(BaseHandlerAdmin):
    def task(self, isAdmin, s):
        

        response = s.data.individuals(None)
        individuals = response[0]
        initial_cursor = response[1]

        template_variables = {"individuals" : individuals, "initial_cursor" : initial_cursor}
        self.response.write(
           template.render('pages/all_individuals.html', template_variables))

class AllTeams(BaseHandlerAdmin):
    def task(self, isAdmin, s):
        isAdmin, s = tools.checkAuthentication(self, True)

        response = s.data.teams(None)
        teams = response[0]
        initial_cursor = response[1]

        template_variables = {"teams":teams, "initial_cursor" : initial_cursor}
        self.response.write(
                template.render('pages/all_teams.html', template_variables))

class Contact(BaseHandlerAdmin):
    def task(self, isAdmin, s):
        contact_key = self.request.get("c")
        c = tools.getKey(contact_key).get()

        response = c.data.donations(None)
        donations = response[0]
        initial_cursor = response[1]

        template_variables = {"c" : c, "s" : s, "donations" : donations, "initial_cursor" : initial_cursor}
        self.response.write(
           template.render('pages/contact.html', template_variables))

class Container(BaseHandler):
    def task(self, isAdmin, s):
        username = tools.getUsername(self)

        try:
            template_variables = {"settings" : s.key.urlsafe(), "username" : username}
        except:
            self.redirect("/login")

        if isAdmin == True:
            self.response.write(
                template.render('pages/container.html', template_variables))

        elif isAdmin == False:
            self.response.write(
                template.render('pages/container_ind.html', template_variables))
        
class Dashboard(BaseHandlerAdmin):
    def task(self, isAdmin, s):
        isAdmin, s = tools.checkAuthentication(self, True)

        vals = s.data.one_week_history

        past_donations = vals[0]
        past_money = str(vals[1])

        template_variables = {"num_open_donations" : s.data.num_open_donations, "past_donations" : past_donations, "past_money" : past_money}
        self.response.write(
            template.render('pages/dashboard.html', template_variables))

class Deposit(BaseHandlerAdmin):
    def task(self, isAdmin, s):
        isAdmin, s = tools.checkAuthentication(self, True)

        #WARNING - this is a really complicated and kind of a hacked-together
        #solution. I didn't understand it the day after I wrote it.
        # ... But it works. 

        deposit_key = self.request.get("d")
        deposit = tools.getKey(deposit_key).get()

        entity_keys = deposit.entity_keys
        total_amount = tools.toDecimal(0)
        general_fund = tools.toDecimal(0)

        donations = []
        team_breakout = {}

        for k in entity_keys:
            d = k.get()
            if d != None:
                donations.append(d)

                total_amount += d.amount_donated

                if d.team:
                    t = d.team.get()
                    try:
                        team_breakout[t.name]
                    except:
                        team_breakout[t.name] = [tools.toDecimal(0), []]

                    team_breakout[t.name][0] += d.amount_donated

                    if d.individual:
                        i = d.individual.get()
                        array = [i.name, d.amount_donated]

                        team_breakout[t.name][1].append(array)
                else:
                    #Add count to general fund
                    general_fund += d.amount_donated

        team_breakout["General Fund"] = [tools.toDecimal(general_fund), []]

        new_team_breakout = {}
        for k,v in team_breakout.items():
            name = k
            amount_donated = v[0]
            array = v[1]
            new_array = []

            for a in array:
                string = a[0] + " ($" + str(a[1]) + ")"
                new_array.append(string)

            new_team_breakout[str(name) + " ($" + str(amount_donated) + ")"] = new_array

        template_variables = {"d" : deposit, "donations" : donations, "team_breakout" : new_team_breakout,
                "total_amount" : total_amount}
        self.response.write(
                template.render('pages/deposit.html', template_variables))

class DonatePage(webapp2.RequestHandler):
    def get(self):
        self.response.headers['Access-Control-Allow-Origin'] = '*'
        
        settings = self.request.get("s")

        try:
            s = tools.getKey(settings).get()

            template_variables = {"s" : s}
            self.response.write(
                    template.render('pages/public_pages/pub_donate.html', template_variables))
            
        except:
            self.response.write("Sorry, this URL triggered an error.  Please try again.")

class DonorReport(BaseHandlerAdmin):
    def task(self, isAdmin, s):
        try:
            isAdmin, s = tools.checkAuthentication(self, True)

            contact_key = self.request.get("c")
            year = int(self.request.get("y"))

            if contact_key == "" or year == "" or len(str(year)) != 4:
                #Throw an error if you don't have those two pieces of info or if the year isn't a number
                raise Exception("Don't know contact key or year.")

            c = tools.getKey(contact_key).get()
            s = c.settings.get()

            donations = c.data.annual_donations(year)
            donation_total = tools.toDecimal(0)

            for d in donations:
                donation_total += d.amount_donated

            donation_total = "${:,.2f}".format(donation_total)

            template_variables = {"s":s, "c":c, "donations":donations, "year":str(year), "donation_total":str(donation_total), "street":c.address[0], "city":c.address[1], "state":c.address[2], "zip":c.address[3]}

            self.response.write(
                   template.render("pages/letters/donor_report_print.html", template_variables))

        
        except:
            #If there's a malformed URL, give a 500 error
            self.error(500)
            self.response.write(
                   template.render('pages/letters/thankyou_error.html', {}))

class DonorReportSelect(BaseHandlerAdmin):
    def task(self, isAdmin, s):
        isAdmin, s = tools.checkAuthentication(self, True)

        template_variables = {"s" : s}
        self.response.write(
           template.render('pages/donor_report_select.html', template_variables))
        
class ExportContacts(BaseHandlerAdmin):
    def task(self, isAdmin, s):
        isAdmin, s = tools.checkAuthentication(self, True)

        template_variables = {}
        self.response.write(
           template.render('pages/export_contacts.html', template_variables))

class ExportDonations(BaseHandlerAdmin):
    def task(self, isAdmin, s):
        isAdmin, s = tools.checkAuthentication(self, True)

        template_variables = {}
        self.response.write(
           template.render('pages/export_donations.html', template_variables))

class IndividualProfile(BaseHandler):
    def task(self, isAdmin, s):
        

        if isAdmin == True:
            #If an admin, they can get whatever user they want
            i_key = self.request.get("i")

            #if no key specified, go to admin's personal account
            if i_key == "":
                i_key = tools.getUserKey(self)
            else:
                i_key = tools.getKey(i_key)

        else:
            #If a regular user, they can ONLY get their own profile
            i_key = tools.getUserKey(self)
        
        i = i_key.get()
        logging.info("Getting profile page for: " + i.name)

        #Creating a blobstore upload url
        upload_url = blobstore.create_upload_url('/ajax/profile/upload')
            
        template_variables = {"s" : s, "i":i, "upload_url" : upload_url, "isAdmin" : isAdmin}
        self.response.write(
           template.render("pages/profile.html", template_variables))

class IndividualWelcome(BaseHandlerAdmin):
    def task(self, isAdmin, s):
        try:
            mode = self.request.get("m")
            individual_key = self.request.get("i")

            if mode == "" or individual_key == "":
                #Throw an error if you don't have those two pieces of info
                raise  Exception("Don't know mode or individual_key.")

            i = tools.getKey(individual_key).get()
            s = tools.getKey(i.settings).get()

            template_variables = {"s": s, "i" : i}
            self.response.write(
               template.render('pages/letters/individual.html', template_variables))
        
        except:
            #If there's a malformed URL, give a 500 error
            self.error(500)
            self.response.write(
                   template.render('pages/letters/thankyou_error.html', {}))

class Login(webapp2.RequestHandler):  
    def get(self):
        self.session = get_current_session()

        #Flash message
        message = tools.getFlash(self)

        #Delete existing session if it exists
        self.session.terminate()

        template_variables = {"flash" : message}
        self.response.write(
            template.render('pages/login.html', template_variables))

    def post(self):
        self.session = get_current_session()

        email = self.request.get("email")
        password = self.request.get("password")

        authenticated, user = tools.checkCredentials(self, email, password)

        if authenticated == True:
            logging.info("Authenticated: " + str(authenticated) + " and User: " + str(user.name))
            
            #Log in
            self.session["key"] = str(user.key.urlsafe())
            self.redirect("/")

        else:
            #Invalid login
            logging.info("Incorrect login.")
            tools.setFlash(self, "Whoops, that didn't get you in. Try again.")
            self.redirect("/login")

class Logout(webapp2.RequestHandler):
    def get(self):
        self.session = get_current_session()
        self.session.terminate()

        self.redirect("/login")

class MergeContacts(BaseHandlerAdmin):
    def task(self, isAdmin, s):
        

        template_variables = {}
        self.response.write(
           template.render('pages/merge_contacts.html', template_variables))

class NewContact(BaseHandlerAdmin):
    def task(self, isAdmin, s):
        

        template_variables = {}
        self.response.write(
           template.render('pages/new_contact.html', template_variables))

class NewIndividual(BaseHandlerAdmin):
    def task(self, isAdmin, s):
        isAdmin, s = tools.checkAuthentication(self, True)

        template_variables = {"teams":s.data.all_teams}
        self.response.write(
                template.render('pages/new_individual.html', template_variables))

class NewTeam(BaseHandlerAdmin):
    def task(self, isAdmin, s):
        isAdmin, s = tools.checkAuthentication(self, True)

        template_variables = {}
        self.response.write(
                template.render('pages/new_team.html', template_variables))

class NotAuthorized(webapp2.RequestHandler):
    def get(self):
        template_variables = {}
        self.response.write(
           template.render('pages/not_authorized.html', template_variables))

class OfflineDonation(BaseHandlerAdmin):
    def task(self, isAdmin, s):
        
        i = tools.getUserKey(self).get()

        template_variables = {"teams":None, "individual_name" : i.name, 
                "individual_key" : i.key.urlsafe(), "teams" : s.data.all_teams}

        self.response.write(
                template.render('pages/offline.html', template_variables))

class ReviewQueue(BaseHandlerAdmin):
    def task(self, isAdmin, s):
        isAdmin, s = tools.checkAuthentication(self, True)

        #Get open donations
        response = s.data.open_donations(None)

        donations = response[0]
        initial_cursor = response[1]

        template_variables = {"donations":donations, "initial_cursor" : initial_cursor}
        self.response.write(
            template.render('pages/review_queue.html', template_variables))

class ReviewQueueDetails(BaseHandler):
    def task(self, isAdmin, s):
        
        
        donation_key = self.request.get("id")
        if donation_key == "":
        #If they didn't type any arguments into the address bar - meaning it didn't come from the app
            tools.giveError(self, 500)
        else:
            #Getting donation by its key (from address bar argument)
            d = tools.getKey(donation_key).get()

            i_key = tools.getUserKey(self)
            i = i_key.get()

            template_variables = {"d":d, "s":s, "i":i}
            self.response.write(
                    template.render('pages/rq_details.html', template_variables))

class Settings(BaseHandlerAdmin):
    def task(self, isAdmin, s):
        isAdmin, s = tools.checkAuthentication(self, True)

        template_variables = {"s" : s}
        self.response.write(
           template.render('pages/settings.html', template_variables))

class SpreadsheetGenerator(BaseHandlerAdmin):
    def task(self, isAdmin, s):
        isAdmin, s = tools.checkAuthentication(self, True)

        #Initialize a xlwt Excel file
        wb = Workbook()
        ws0 = wb.add_sheet('Sheet 1')

        add_donation_total = False

        action = self.request.get("e")
        if action == "contacts" or action == "recurring_donors" or action == "team_contacts":
            if action == "contacts":
                #Get all donations from the datastore
                all_contacts = s.data.all_contacts
                filename = str(s.name) + "-Contacts"

            elif action == "recurring_donors":
                all_contacts = s.data.recurring_donors
                filename = str(s.name) + "-RecurringDonors"
                add_donation_total = True
                
            elif action == "team_contacts":
                team_key = self.request.get("tk")
                team_key = tools.getKey(team_key)
                
                all_contacts = s.data.team_donors(team_key)
                filename = str(s.name) + "-TeamDonors"
            
            #Write headers
            ws0.write(0, 0, "Name")
            ws0.write(0, 1, "Email")
            ws0.write(0, 2, "Notes")
            ws0.write(0, 3, "Street")
            ws0.write(0, 4, "City")
            ws0.write(0, 5, "State")
            ws0.write(0, 6, "ZIP")
            ws0.write(0, 7, "Phone")

            if add_donation_total == True:
                ws0.write(0, 8, "Donation Total")
            
            
            current_line = 1
            for c in all_contacts:
                if c.address and c.address != "None":
                    a = c.address
                else:
                    a = ["", "", "", ""]

                ws0.write(current_line, 0, c.name)
                ws0.write(current_line, 1, c.email)
                ws0.write(current_line, 2, str(c.notes))
                ws0.write(current_line, 3, a[0])
                ws0.write(current_line, 4, a[1])
                ws0.write(current_line, 5, a[2])
                ws0.write(current_line, 6, a[3])
                ws0.write(current_line, 7, c.phone)

                if add_donation_total == True:
                    ws0.write(current_line, 8, "$" + str(c.data.recurring_donation_total))
                    
                current_line += 1
        
        else:
            tools.giveError(self, 400)
 
        # HTTP headers to force file download
        self.response.headers['Content-Type'] = 'application/ms-excel'
        self.response.headers['Content-Transfer-Encoding'] = 'Binary'
        self.response.headers['Content-disposition'] = 'attachment; filename="' + filename + ".xls" +  '"'
 
        # output to user
        wb.save(self.response.out)

class TeamMembers(BaseHandlerAdmin):
    def task(self, isAdmin, s):
        isAdmin, s = tools.checkAuthentication(self, True)
        
        team_key = self.request.get("t")
        t = tools.getKey(team_key).get()

        template_variables = {"t":t}
        self.response.write(
           template.render('pages/team_members.html', template_variables))

class ThankYou(webapp2.RequestHandler):
    def get(self):
        try:
            mode = self.request.get("m")
            donation_key = self.request.get("id")

            if mode == "" or donation_key == "":
                #Throw an error if you don't have those two pieces of info
                raise Exception("Don't know mode or donation key.")

            d = tools.getKey(donation_key).get()
            date = tools.convertTime(d.donation_date).strftime("%B %d, %Y")
            s = d.settings.get()

            if d.individual:
                individual_name = d.individual.get().name
            elif d.team:
                individual_name = d.team.get().name
            else:
                individual_name = None

            template_variables = {"s": s, "d" : d, "c" : d.contact, "date" : date, "individual_name" : individual_name}

            if mode == "w":
                template_location= "pages/letters/thanks_live.html"

            elif mode == "p":
                template_location= "pages/letters/thanks_print.html"

            elif mode == "e":
                who = "http://ghidonations.appspot.com"

                template_variables["see_url"] = d.confirmation.see_url(who)
                template_variables["print_url"] = d.confirmation.print_url(who)

                template_location = "pages/letters/thanks_email.html"

            self.response.write(
                   template.render(template_location, template_variables))
        
        except:
            #If there's a malformed URL, give a 500 error
            self.error(500)
            self.response.write(
                   template.render('pages/letters/thankyou_error.html', {}))

class UndepositedDonations(BaseHandlerAdmin):
    def task(self, isAdmin, s):
        isAdmin, s = tools.checkAuthentication(self, True)

        template_variables = {"donations" : s.data.undeposited_donations}
        self.response.write(
                template.render('pages/undeposited_donations.html', template_variables))

class UpdateProfile(blobstore_handlers.BlobstoreUploadHandler):
    def post(self):
        #Has a new image been selected?
        change_image = True
        try:
            upload_files = self.get_uploads('new_photo')
            blob_info = upload_files[0]
        except:
            change_image = False

        individual_key = self.request.get("individual_key")
        name = self.request.get("name")
        email = self.request.get("email")
        team = self.request.get("team_list")
        description = quopri.decodestring(self.request.get("description"))
        password = self.request.get("password")
        show_donation_page = self.request.get("show_donation_page")

        if show_donation_page == "on":
            show_donation_page = True
        elif show_donation_page == "":
            show_donation_page = False

        i = tools.getKey(individual_key).get()

        if change_image == True:
            new_blobkey = str(blob_info.key())
        else:
            new_blobkey = None

        logging.info("Saving profile for: " + name)

        i.update(name, email, team, description, new_blobkey, password, show_donation_page)

        self.redirect("/#profile?i=" + individual_key)

class IPN(BaseHandlerAdmin):
    def task(self, isAdmin, s):
        self.response.write("GHI Donations - PayPal IPN Handler")

    def post(self):
        #Below URL used for the live version.
        PP_URL = "https://www.paypal.com/cgi-bin/webscr"

        #Below URL used for testing with the sandbox - if this is uncommented, all real
        #donations will not be authenticated. ONLY use with dev versions.
        # PP_URL = "https://www.sandbox.paypal.com/cgi-bin/webscr"

        #Gets all account emails from Settings data models
        #to authenticate PayPal (don't accept payment from unknown)
        all_account_emails = tools.getAccountEmails(self)

        parameters = None
        if self.request.POST:
            parameters = self.request.POST.copy()
        if self.request.GET:
            parameters = self.request.GET.copy()

        payment_status = self.request.get("payment_status")
        logging.info("Payment status: " + payment_status)

        # Check payment is completed, not Pending or Failed.
        # if self.request.get('payment_status') == 'Completed':
        # else:
        #     self.response.write('Error, sorry. The parameter payment_status was not Completed.')

        logging.info("All parameters: " + str(parameters))

        # Check the IPN POST request came from real PayPal, not from a fraudster.
        if parameters:
            parameters['cmd']='_notify-validate'
            params = urllib.urlencode(parameters)
            status = urlfetch.fetch(
                        url = PP_URL,
                        method = urlfetch.POST,
                        payload = params,
                       ).content
            if not status == "VERIFIED":
                logging.debug("PayPal returned status:" + str(status))
                logging.debug('Error. The request could not be verified, check for fraud.')
                parameters['homemadeParameterValidity']=False

        #Comparing receiver email to list of allowed email addresses
        try:
            receiver_email = parameters['receiver_email']
            authenticated = False
            settings = None
        
            #If the receiver_email isn't in the database, this will fail
            settings = all_account_emails[receiver_email]
            authenticated = True
            logging.info("Getting payment to account: " + receiver_email + ", #: " + settings)

        except:
            authenticated = False
            logging.info("No match for incoming payment email address. Not continuing.")

        # Make sure money is going to the correct account - otherwise fraudulent
        if authenticated == True:
            #Currency of the donation
            #currency = parameters['mc_currency']

            s = tools.getKey(settings).get()
            ipn_data = str(parameters)

            #Email and payer ID  numbers
            try:
                email = parameters['payer_email']
            except:
                email = None
            
            try:
                name = parameters['first_name'] + " " + parameters['last_name']
            except:
                name = "Anonymous Donor"

            #Check if an address was given by the donor
            try:
                #Stich all the address stuff together
                address = [parameters['address_street'], parameters['address_city'], parameters['address_state'], parameters['address_zip']]
                
            except:
                address = None

            #Reading designation and notes values encoded in JSON from
            #donate form
            decoded_custom = None

            try:
                decoded_custom = json.loads(parameters["custom"])

                team_key = tools.getKey(decoded_custom[0])
                individual_key = tools.getKey(decoded_custom[1])
                special_notes = decoded_custom[2]

                if s.exists.entity(team_key) == False:
                    raise  Exception("Bad key.")
                if s.exists.entity(individual_key) == False:
                    raise  Exception("Bad key.")

            except:
                logging.info("Excepted on designation.")
                team_key = None
                individual_key = None
                special_notes = None

            try:
                cover_trans = decoded_custom[3]
                email_subscr = decoded_custom[4]
            except:
                cover_trans = False
                email_subscr = False


            confirmation_amount = tools.toDecimal(0)
            amount_donated = tools.toDecimal(0)
            try:
                confirmation_amount = parameters['mc_gross']
                amount_donated = float(parameters['mc_gross']) - float(parameters['mc_fee'])

            except:
                pass
                
            #Find out what kind of payment this was - recurring, one-time, etc.
            try:
                payment_type = parameters['txn_type']
                logging.info("Txn_type not available, so continuing with payment status")
            except:
                payment_type = payment_status

            if payment_type == "recurring_payment_profile_created" or payment_type == "subscr_signup":
                logging.info("This is the start of a recurring payment. Create info object.")

                payment_id = parameters['subscr_id']

                #Duration between payments
                duration = "recurring"

                # s.create.recurring_donation(payment_id, duration, ipn_data)
                
            elif payment_type == "recurring_payment" or payment_type == "subscr_payment":
                logging.info("This is a recurring donation payment.")
                
                payment_id = parameters['subscr_id']
                payment_type = "recurring"
                
                #Create a new donation
                s.create.donation(name, email, amount_donated, confirmation_amount, address, team_key, individual_key, True, payment_id, special_notes, payment_type, email_subscr, ipn_data)

            elif payment_type == "web_accept":
                logging.info("This is a one-time donation.")

                if payment_status == "Completed":
                    payment_id = parameters['txn_id']

                    #Create a new donation
                    s.create.donation(name, email, amount_donated, confirmation_amount, address, team_key, individual_key, True, payment_id, special_notes, "one-time", email_subscr, ipn_data)

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
                    donation = models.Donation.gql("WHERE payment_id = :t", t=parameters["txn_id"])
                    donation_key = donation[0].key()

                    donation_key.delete()
                    logging.info("Refund detected and donation deleted. (" + donation_key.urlsafe() + ")")
                except:
                    logging.info("Donation tried to be deleted, but failed. Most likely already deleted.")
                
            try:
                logging.info("Recording IPN")
                logging.info("Payment type: " + payment_type)
                logging.info("Name: " + name)
                logging.info("Email: " + email)
                logging.info("Amount donated: " + str(amount_donated))
            except:
                logging.error("Failed somewhere in the logs.")
            
app = webapp2.WSGIApplication([
       ('/ajax/allcontacts', AllContacts),
       ('/ajax/alldeposits', AllDeposits),
       ('/ajax/allindividuals', AllIndividuals),
       ('/ajax/allteams', AllTeams),       
       ('/ajax/contact', Contact),       
       ('/', Container),      
       ('/ajax/dashboard', Dashboard),       
       ('/ajax/deposit', Deposit),       
       ('/donate', DonatePage),
       ('/reports/donor', DonorReport),
       ('/ajax/donorreport', DonorReportSelect),
       ('/ajax/exportcontacts', ExportContacts),
       ('/ajax/exportdonations', ExportDonations),
       ('/ajax/profile', IndividualProfile),
       ('/login', Login),
       ('/logout', Logout),
       ('/ajax/mergecontacts', MergeContacts),
       ('/ajax/newcontact', NewContact),
       ('/ajax/newindividual', NewIndividual),
       ('/ajax/newteam', NewTeam),
       ('/ajax/notauthorized', NotAuthorized),
       ('/ajax/offline', OfflineDonation),
       ('/ajax/review', ReviewQueue),
       ('/ajax/reviewdetails', ReviewQueueDetails),
       ('/ajax/settings', Settings),
       ('/ajax/spreadsheet', SpreadsheetGenerator),
       ('/ajax/teammembers', TeamMembers),
       ('/thanks', ThankYou),
       ('/ajax/undeposited', UndepositedDonations),
       ('/ajax/profile/upload', UpdateProfile),
       ('/ipn', IPN)],
       debug=True)

app = appengine_config.webapp_add_wsgi_middleware(app)
app = appengine_config.recording_add_wsgi_middleware(app)