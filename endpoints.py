import logging, json, datetime, appengine_config, webapp2
from google.appengine.api import taskqueue

import GlobalUtilities as tools
import DataModels as models

# Cloud Endpoints
from google.appengine.ext import endpoints
from protorpc import remote
from endpoints_messages import *

endpoints_client_id = "AIzaSyB7k0LsUXibTJHkCx_D3MA0HT6tQAtYZAo"
endpoints_description = "GHI Donations API"
endpoints_clients = [endpoints_client_id, endpoints.API_EXPLORER_CLIENT_ID]

@endpoints.api(name='ghidonations', version='v1',
               description=endpoints_description,
               allowed_client_ids=endpoints_clients)
class EndpointsAPI(remote.Service):

## -- Globalhopeindia.org Utility Functions -- ##

    # public.all_teams
    @endpoints.method(AllTeams_In, AllTeams_Out, path='public/all_teams',
                    http_method='GET', name='public.all_teams')
    def public_all_teams(self, req):
        s = tools.getKey(req.settings_key).get()

        all_teams = []
        for t in s.data.display_teams:
            team = Team_Data(name=t.name, key=t.key.urlsafe())          
            all_teams.append(team)
        
        return AllTeams_Out(all_teams=all_teams)

    # public.individual_info
    @endpoints.method(IndividualInfo_In, IndividualInfo_Out, path='public/individual_info',
                    http_method='GET', name='public.individual_info')
    def public_individual_info(self, req):
        i = tools.getKey(req.individual_key).get()
        t_key = tools.getKey(req.team_key)
        info = i.data.info(t_key)

        return IndividualInfo_Out(image_url=info[0], name=info[1], description=info[2], 
                                percentage=info[3], message=info[4])

    # public.team_info
    @endpoints.method(TeamInfo_In, TeamInfo_Out, path='public/team_info',
                    http_method='GET', name='public.team_info')
    def public_team_info(self, req):
        t = tools.getKey(req.team_key).get()
        
        info_list = []
        m_list = t.data.members_list
        for m in m_list:
            info = TeamInfo_Data(name=m[0], photo_url=m[1], tl_key=m[2])
            info_list.append(info)

        return TeamInfo_Out(info_list=info_list)


#### ---- Data Access ---- ####
    # get.contacts
    @endpoints.method(Query_In, Contacts_Out, path='get/contacts',
                    http_method='GET', name='get.contacts')
    def get_contacts(self, req):
        s = tools.getSettingsKey(self).get()

        results = s.search.contact(req.query, query_cursor=req.query_cursor)
        logging.info("Getting contacts with query: " + req.query)

        contacts = []
        new_cursor = tools.getWebsafeCursor(results[1])

        for c in results[0]:
            f = c.fields
            contact = Contact_Data(key=f[0].value, name=f[1].value, email=f[2].value)
            contacts.append(contact)

        return Contacts_Out(contacts=contacts, new_cursor=new_cursor)

    @endpoints.method(GetContactDonations_In, Donations_Out, path='get/contact_donations',
                    http_method='GET', name='get.contact_donations')
    def get_contact_donations(self, req):
        s = tools.getSettingsKey(self).get()
        query = "contact_key:" + str(req.contact_key)

        results = s.search.donation(query, query_cursor=req.query_cursor)
        logging.info("Getting contact donations with query: " + query)

        donations = []
        new_cursor = tools.getWebsafeCursor(results[1])

        for d in results[0]:
            f = d.fields

            donation = Donation_Data(key=f[0].value, formatted_donation_date=f[9].value, name=f[2].value, email=f[3].value,
                 payment_type=f[5].value, amount_donated=tools.moneyAmount(f[4].value))

            donations.append(donation)

        return Donations_Out(donations=donations, new_cursor=new_cursor)

    # get.deposits
    @endpoints.method(Query_In, Deposits_Out, path='get/deposits',
                    http_method='GET', name='get.deposits')
    def get_deposits(self, req):
        s = tools.getSettingsKey(self).get()

        results = s.search.deposit(req.query, query_cursor=req.query_cursor)
        logging.info("Getting deposits with query: " + req.query)

        deposits = []
        new_cursor = tools.getWebsafeCursor(results[1])

        for de in results[0]:
            f = de.fields

            deposit = Deposit_Data(key=f[0].value, time_deposited=f[1].value)
            deposits.append(deposit)

        return Deposits_Out(deposits=deposits, new_cursor=new_cursor)

    # get.donations
    @endpoints.method(Query_In, Donations_Out, path='get/donations',
                    http_method='GET', name='get.donations')
    def get_donations(self, req):
        s = tools.getSettingsKey(self).get()

        results = s.search.donation(req.query, query_cursor=req.query_cursor)
        logging.info("Getting donations with query: " + req.query)

        donations = []
        new_cursor = tools.getWebsafeCursor(results[1])

        for d in results[0]:
            f = d.fields

            donation = Donation_Data(key=f[0].value, formatted_donation_date=f[9].value, name=f[2].value, email=f[3].value,
                 payment_type=f[5].value, amount_donated=tools.moneyAmount(f[4].value))

            donations.append(donation)

        return Donations_Out(donations=donations, new_cursor=new_cursor)

    # get.individuals
    @endpoints.method(Query_In, Individuals_Out, path='get/individuals',
                    http_method='GET', name='get.individuals')
    def get_individuals(self, req):
        s = tools.getSettingsKey(self).get()
        
        results = s.search.individual(req.query, query_cursor=req.query_cursor)
        logging.info("Getting individuals with query: " + req.query)

        individuals = []
        new_cursor = tools.getWebsafeCursor(results[1])

        for i in results[0]:
            f = i.fields

            individual = Individual_Data(key=f[0].value, name=f[1].value, email=f[2].value, amount_donated=tools.moneyAmount(f[4].value))
            individuals.append(individual)

        return Individuals_Out(individuals=individuals, new_cursor=new_cursor)

    # mailchimp.lists
    @endpoints.method(MailchimpLists_In, MailchimpLists_Out, path='mailchimp/lists',
                    http_method='GET', name='mailchimp.lists')
    def mailchimp_lists(self, req):
        repsonse = tools.getMailchimpLists(self, req.mc_apikey)
        mc_lists = None
        error_message = None

        if response[0] == True:
            mc_lists = json.dumps(response[1])
        else:
            mc_lists = None
            error_message = response[1]

        return MailchimpLists_Out(success=response[0], mc_lists=mc_lists, error_message=error_message)

    # get.teams
    @endpoints.method(Query_In, Teams_Out, path='get/teams',
                    http_method='GET', name='get.teams')
    def getTeams(self, req):
        s = tools.getSettingsKey(self).get()

        results = s.search.team(req.query, query_cursor=req.query_cursor)
        logging.info("Getting teams with query: " + req.query)

        teams = []
        new_cursor = tools.getWebsafeCursor(results[1])

        for t in results[0]:
            f = t.fields
            
            team = Team_Data(key=f[0].value, name=f[1].value)
            teams.append(team)

        return Teams_Out(teams=teams, new_cursor=new_cursor)

    # get.team_members
    @endpoints.method(GetTeamMembers_In, Teams_Out, path='get/team_members',
                    http_method='GET', name='get.team_members')
    def get_team_members(self, req):
        s = tools.getSettingsKey(self).get()
        query = "team_key:" + str(req.team_key)

        results = s.search.individual(query, query_cursor=req.query_cursor)
        logging.info("Getting team members with query: " + query)

        individuals = []
        new_cursor = tools.getWebsafeCursor(results[1])

        for i in results[0]:
            f = i.fields

            individual = Individual_Data(key=f[0].value, name=f[1].value, email=f[2].value, raised=tools.moneyAmount(f[4].value))
            individuals.append(individual)

        return Individual_Out(individuals=individuals, new_cursor=new_cursor)

    # get.individual_donations
    @endpoints.method(GetIndividualDonations_In, Donations_Out, path='semi/get/individual_donations',
                    http_method='GET', name='semi.get.individual_donations')
    def semi_get_individual_donations(self, req):
        s = tools.getSettingsKey(self).get()
        query = "individual_key:" + str(req.individual_key)

        results = s.search.donation(query, query_cursor=req.query_cursor)
        logging.info("Getting individual donations with query: " + query)

        donations = []
        new_cursor = tools.getWebsafeCursor(results[1])

        for d in results[0]:
            f = d.fields

            donation = Donation_Data(key=f[0].value, formatted_donation_date=f[9].value, name=f[2].value, email=f[3].value,
                 payment_type=f[5].value, amount_donated=tools.moneyAmount(f[4].value))

            donations.append(donation)

        return Donations_Out(donations=donations, new_cursor=new_cursor)

    # semi.get.team_members
    @endpoints.method(SemiGetTeamMembers_In, SemiGetTeamMembers_Out, path='semi/get/team_members',
                    http_method='GET', name='semi.get.team_members')
    def semi_get_team_members(self, req):
    # Returns team information
        t = tools.getKey(req.team_key).get()
        members_list = t.data.members_list

        members = []
        for m in members_list:
            member = SemiTeamMembers_Data(key=m[0], name=m[2])
            members.append(member)

        return SemiGetTeamMembers_Out(members=members)

# #### ---- Data creation/updating ---- ####
    # donation.mark_unreviewed
    @endpoints.method(DonationMarkUnreviewed_In, SuccessMessage_Out, path='donation/mark_unreviewed',
                    http_method='POST', name='donation.mark_unreviewed')
    def donation_mark_unreviewed(self, req):
        message = "Donation marked as unreviewed"
        success = True

        d = tools.getKey(req.donation_key).get()
        d.review.markUnreviewed()

        return SuccessMessage_Out(success=success, message=message)

    # new.contact
    @endpoints.method(NewContact_In, SuccessMessage_Out, path='new/contact',
                    http_method='POST', name='new.contact')
    def new_contact(self, req):
        message = "<b>" + req.name + "</b> created"
        success = True

        s = tools.getSettingsKey(self).get()
        contact_exists = s.exists.contact(req.email)

        address = [req.address.street, req.address.city, req.address.state, req.address.zipcode]

        if contact_exists[0] == False:
            s.create.contact(req.name, req.email, req.phone, address, req.notes, True)

        else:
            #If this email address already exists for a user
            message = "This contact already exists, but we updated their information."

            c = exists[1].get()
            contact.update(name, email, phone, notes, address)

        return SuccessMessage_Out(success=success, message=message)

    # new.impression
    @endpoints.method(NewImpression_In, SuccessMessage_Out, path='new/impression',
                    http_method='POST', name='new.impression')
    def newImpression(self, req):
        message = "Impression saved"
        success = True

        c = tools.getKey(req.contact_key).get()
        c.create.impression(req.impression, req.notes)

        #Return message to confirm 
        return_vals = [success, message]
        return return_vals

#     def newIndividual(self, name, team_key, email, password, admin):
#         message = "<b>" + name + "</b> created"
#         success = True

#         s = tools.getSettingsKey(self).get()
#         exists = s.exists.individual(email)

#         if exists[0] == False:
#             if email == "":
#                 email = None

#             if team_key == "team":
#                 team_key = None

#             s.create.individual(name, tools.getKey(team_key), email, password, admin)

#         else:
#             #If this email address already exists for a user
#             message = "Sorry, but this email address is already being used."
#             success = False

#         #Return message to confirm 
#         return_vals = [success, message]
#         return return_vals

#     def newTeam(self, name):
#         message = "<b>" + name + "</b> created"
#         success = True

#         s = tools.getSettingsKey(self).get()
#         s.create.team(name)

#         #Return message to confirm 
#         return_vals = [success, message]
#         return return_vals

#     def offlineDonation(self, name, email, amount_donated, notes, address, team_key, individual_key, add_deposit):
#         message = "Offline donation created"
#         success = True

#         s = tools.getSettingsKey(self).get()

#         if address == "":
#             address = None
#         else:
#             address = json.loads(address)

#         if team_key == "" or team_key == "general":
#             team_key = None
#         else:
#             team_key = tools.getKey(team_key)

#         if individual_key == "" or individual_key == None or individual_key == "none":
#             individual_key = None
#         else:
#             individual_key = tools.getKey(individual_key)
            

#         s.create.donation(name, email, amount_donated, amount_donated, address, team_key, individual_key, add_deposit, "", "", "offline", False, None)

#         #Return message to confirm 
#         return_vals = [success, message]
#         return return_vals
    
#     def updateDonation(self, donation_key, notes, team_key, individual_key, add_deposit):
#         message = "Donation has been saved"
#         success = True

#         d = tools.getKey(donation_key).get()

#         if team_key == "general":
#             team_key = None
#         elif team_key:
#             team_key = tools.getKey(team_key)

#         if individual_key:
#             individual_key = tools.getKey(individual_key)

#         d.update(notes, team_key, individual_key, add_deposit)

#         #Return message to confirm 
#         return_vals = [success, message]
#         return return_vals

#     def updateContact(self, contact_key, name, email, phone, notes, address):
#         message = "Contact has been saved"
#         success = True

#         c = tools.getKey(contact_key).get()
#         address = json.loads(address)
#         c.update(name, email, phone, notes, address)
        
#         #Return message to confirm 
#         return_vals = [success, message]
#         return return_vals

#     def updateSettings(self, name, email, mc_use, mc_apikey, mc_donorlist, paypal_id, impressions, amount1, amount2, amount3, amount4, use_custom, confirmation_header, confirmation_info, confirmation_footer, confirmation_text, donor_report_text):
#         message = "Settings have been updated"
#         success = True

#         s = tools.getSettingsKey(self).get()
#         s.update(name, email, mc_use, mc_apikey, mc_donorlist, paypal_id, impressions, amount1, amount2, amount3, amount4, use_custom, confirmation_header, confirmation_info, confirmation_footer, confirmation_text, donor_report_text)

#         #Return message to confirm 
#         return_vals = [success, message]
#         return return_vals

#     def updateTeam(self, team_key, name, show_team):
#         message = "Team has been updated"
#         success = True

#         t = tools.getKey(team_key).get()
#         t.update(name, show_team)

#         #Return message to confirm 
#         return_vals = [success, message]
#         return return_vals

# #### ---- Contact merge ---- ####
#     def mergeContacts(self, contact1, contact2):
#         message = "Contacts merged"
#         success = True

#         c1 = tools.getKey(contact1)
#         c2 = tools.getKey(contact2)

#         tools.mergeContacts(c1, c2)

#         #Return message to confirm 
#         return_vals = [success, message]
#         return return_vals

# #### ---- Search ---- ####
#     def getContactsJSON(self):
#         s = tools.getSettingsKey(self).get()
#         return s.data.contactsJSON

# #### ---- Donation depositing ---- ####
#     def depositDonations(self, donation_keys):
#         message = "Donations deposited."
#         success = True

#         if donation_keys != []:
#             s = tools.getSettingsKey(self).get()
#             s.deposits.deposit(donation_keys)

#         else:
#             message = "No donations to deposit."
#             success = False

#         #Return message to confirm 
#         return_vals = [success, message]
#         return return_vals

#     def removeFromDeposits(self, donation_keys):
#         message = "Donations removed from deposits."
#         success = True

#         s = tools.getSettingsKey(self).get()

#         donation_keys = tools.strArrayToKey(self, donation_keys)
#         s.deposits.remove(donation_keys)

#         #Return message to confirm 
#         return_vals = [success, message]
#         return return_vals

# #### ---- Confirmation Letters ---- ####
#     def emailReceipt(self, donation_key):
#         message = "Email sent"
#         success = True

#         d = tools.getKey(donation_key).get()

#         #Email receipt to donor
#         d.review.archive()
#         d.confirmation.task(60)

#         #Return message to confirm
#         return_vals = [success, message]
#         return return_vals

#     def printReceipt(self, donation_key):
#         message = "Receipt open for printing"
#         success = True

#         d = tools.getKey(donation_key).get()

#         #Print receipt to donor
#         d.review.archive()
#         print_url = d.confirmation.print_url(None)

#         #Return message to confirm
#         return_vals = [success, message, print_url]
#         return return_vals

#     def archiveDonation(self, donation_key):
#         message = "Donation archived"
#         success = True

#         d = tools.getKey(donation_key).get()
#         d.review.archive()

#         #Return message to confirm
#         return_vals = [success, message]
#         return return_vals

#     def emailAnnualReport(self, contact_key, year):
#         message = "Annual report sent"
#         success = True

#         taskqueue.add(queue_name="annualreport", url="/tasks/annualreport", params={'contact_key' : contact_key, 'year' : year})

#         #Return message to confirm
#         return_vals = [success, message]
#         return return_vals

# #### ---- Data deletion ---- ####
#     def deleteDonation(self, donation_key):
#         message = "Donation deleted"
#         success = True

#         tools.getKey(donation_key).delete()

#         #Return message to confirm
#         return_vals = [success, message]
#         return return_vals

#     def deleteContact(self, contact_key):
#         message = "Contact deleted"
#         success = True

#         tools.getKey(contact_key).delete()

#         #Return message to confirm
#         return_vals = [success, message]
#         return return_vals

#     def deleteTeam(self, team_key):
#         message = "Team deleted"
#         success = True

#         tools.getKey(team_key).delete()

#         #Return message to confirm
#         return_vals = [success, message]
#         return return_vals

#     def semi_deleteIndividual(self, individual_key):
#         message = "Individual deleted"
#         success = True

#         user_key = tools.getUserKey(self)
        
#         i_key = tools.getKey(individual_key)
#         isAdmin = user_key.get().admin

#         if isAdmin == True:
#             i_key.delete()
#         else:
#             if user_key == individual_key:
#                 i_key.delete()
#             else:
#                 #Access denied - non-admin trying to delete someone else
#                 message = "Failed - Access denied"
#                 success = False

#         #Return message to confirm 
#         return_vals = [success, message]
#         return return_vals

app = endpoints.api_server([EndpointsAPI],
                                   restricted=False)