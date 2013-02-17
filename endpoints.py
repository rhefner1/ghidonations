import logging, json, datetime, appengine_config, webapp2
from google.appengine.api import taskqueue

import GlobalUtilities as tools
import DataModels as models

# Cloud Endpoints
from google.appengine.ext import endpoints
from protorpc import remote
import endpoints_messages

endpoints_client_id = ""
endpoints_description = "GHI Donations API"
endpoints_clients = [endpoints_client_id, endpoints.API_EXPLORER_CLIENT_ID]

@endpoints.api(name='ghidonations', version='v1',
               description=endpoints_description,
               allowed_client_ids=endpoints_clients)
class EndpointsAPI(remote.Service):

## -- Globalhopeindia.org Utility Functions -- ##

    # public.all_teams
    def public_all_teams(self, settings_key):
        s = tools.getKey(settings_key).get()

        all_teams = []
        for t in s.data.display_teams:
            team = [t.name, t.key.urlsafe()]           
            all_teams.append(team)
        
        return all_teams

    # public.individual_info
    def public_individual_info(self, team_key, individual_key):
        i = tools.getKey(individual_key).get()
        t_key = tools.getKey(team_key)
        return i.data.info(t_key)

    # public.team_info
    def public_team_info(self, team_key):
        t = tools.getKey(team_key).get()
        return t.data.members_list

#### ---- Data Access ---- ####
    def getContacts(self, query_cursor, query):
        s = tools.getSettingsKey(self).get()

        results = s.search.contact(query, query_cursor=query_cursor)
        logging.info("Getting contacts with query: " + query)

        contacts = []
        new_cursor = tools.getWebsafeCursor(results[1])

        for c in results[0]:
            f = c.fields
            c_dict = {"key" : f[0].value, "name" : f[1].value, "email" : f[2].value}

            contacts.append(c_dict)

        #Return message to confirm 
        return_vals = [contacts, new_cursor]
        return return_vals

    def getContactDonations(self, query_cursor, contact_key):
        s = tools.getSettingsKey(self).get()
        query = "contact_key:" + str(contact_key)

        results = s.search.donation(query, query_cursor=query_cursor)
        logging.info("Getting contact donations with query: " + query)

        donations = []
        new_cursor = tools.getWebsafeCursor(results[1])

        for d in results[0]:
            f = d.fields

            d_dict = {"key" : f[0].value, "formatted_donation_date" : f[9].value, "name" : f[2].value, "email" : f[3].value,
                 "payment_type" : f[5].value, "amount_donated" : tools.moneyAmount(f[4].value)}

            donations.append(d_dict)

        #Return message to confirm 
        return_vals = [donations, new_cursor]
        return return_vals

    def getDeposits(self, query_cursor, query):
        s = tools.getSettingsKey(self).get()

        results = s.search.deposit(query, query_cursor=query_cursor)
        logging.info("Getting deposits with query: " + query)

        deposits = []
        new_cursor = tools.getWebsafeCursor(results[1])

        for de in results[0]:
            f = de.fields
            de_dict = {"key" : f[0].value, "time_deposited" : f[1].value}

            deposits.append(de_dict)

        #Return message to confirm 
        return_vals = [deposits, new_cursor]
        return return_vals

    def getDonations(self, query_cursor, query):
        s = tools.getSettingsKey(self).get()

        results = s.search.donation(query, query_cursor=query_cursor)
        logging.info("Getting donations with query: " + query)

        donations = []
        new_cursor = tools.getWebsafeCursor(results[1])

        for d in results[0]:
            f = d.fields

            d_dict = {"key" : f[0].value, "formatted_donation_date" : f[9].value, "name" : f[2].value, "email" : f[3].value,
                 "payment_type" : f[5].value, "amount_donated" : tools.moneyAmount(f[4].value)}

            donations.append(d_dict)

        #Return message to confirm 
        return_vals = [donations, new_cursor]
        return return_vals

    def getIndividuals(self, query_cursor, query):
        s = tools.getSettingsKey(self).get()
        
        results = s.search.individual(query, query_cursor=query_cursor)
        logging.info("Getting individuals with query: " + query)

        individuals = []
        new_cursor = tools.getWebsafeCursor(results[1])

        for i in results[0]:
            f = i.fields
            i_dict = {"key" : f[0].value, "name" : f[1].value, "email" : f[2].value}

            individuals.append(i_dict)

        #Return message to confirm 
        return_vals = [individuals, new_cursor]
        return return_vals

    def getMailchimpLists(self, mc_apikey):
        return tools.getMailchimpLists(self, mc_apikey)

    def getSettings(self):
        settings = tools.getAccountEmails(self)
        return settings

    def getTeams(self, query_cursor, query):
        s = tools.getSettingsKey(self).get()

        results = s.search.team(query, query_cursor=query_cursor)
        logging.info("Getting teams with query: " + query)

        teams = []
        new_cursor = tools.getWebsafeCursor(results[1])

        for t in results[0]:
            f = t.fields
            i_dict = {"key" : f[0].value, "name" : f[1].value}

            teams.append(i_dict)

        #Return message to confirm 
        return_vals = [teams, new_cursor]
        return return_vals

    def getTeamMembers(self, query_cursor, team_key):
        s = tools.getSettingsKey(self).get()
        query = "team_key:" + str(team_key)

        results = s.search.individual(query, query_cursor=query_cursor)
        logging.info("Getting team members with query: " + query)

        individuals = []
        new_cursor = tools.getWebsafeCursor(results[1])

        for i in results[0]:
            f = i.fields
            i_dict = {"key" : f[0].value, "name" : f[1].value, "email" : f[2].value, "raised" : tools.moneyAmount(f[4].value)}

            individuals.append(i_dict)

        #Return message to confirm 
        return_vals = [individuals, new_cursor]
        return return_vals

    def getTeamDonors(self, team_key):
        s = tools.getSettingsKey(self).get()
        team_key = tools.getKey("ahBkZXZ-Z2hpZG9uYXRpb25zcgoLEgRUZWFtGAIM")
        return s.data.team_donors(team_key)

    def semi_getIndividualDonations(self, query_cursor, individual_key):
        s = tools.getSettingsKey(self).get()
        query = "individual_key:" + str(individual_key)

        results = s.search.donation(query, query_cursor=query_cursor)
        logging.info("Getting individual donations with query: " + query)

        donations = []
        new_cursor = tools.getWebsafeCursor(results[1])

        for d in results[0]:
            f = d.fields

            d_dict = {"key" : f[0].value, "formatted_donation_date" : f[9].value, "name" : f[2].value, "email" : f[3].value,
                 "payment_type" : f[5].value, "amount_donated" : tools.moneyAmount(f[4].value)}

            donations.append(d_dict)

        #Return message to confirm 
        return_vals = [donations, new_cursor]
        return return_vals

    def semi_getTeamMembers(self, team_key):
    # Returns team information
        t = tools.getKey(team_key).get()
        return t.data.members_dict

    def IndividualName(self, individual_key):
        i = tools.getKey(individual_key).get()
        return individual.name

#### ---- Data creation/updating ---- ####
    def donationUnreviewed(self, donation_key):
        message = "Donation marked as unreviewed"
        success = True

        d = tools.getKey(donation_key).get()
        d.review.markUnreviewed()

        #Return message to confirm 
        return_vals = [success, message]
        return return_vals

    def editIndividual(self, name, email, team_list, description):
        message = "Individual saved"
        success = True
        
        i = tools.getKey(individual_key).get()
        i.update(name, email, team_list, description, None)

        #Return message to confirm 
        return_vals = [success, message]
        return return_vals

    def newContact(self, name, email, phone, address, notes):
        message = "<b>" + name + "</b> created"
        success = True

        s = tools.getSettingsKey(self).get()
        contact_exists = s.exists.contact(email)

        address = json.loads(address)

        if contact_exists[0] == False:
            s.create.contact(name, email, phone, address, notes, True)

        else:
            #If this email address already exists for a user
            message = "This contact already exists, but we updated their information."

            c = exists[1].get()
            contact.update(name, email, phone, notes, address)

        #Return message to confirm 
        return_vals = [success, message]
        return return_vals

    def newImpression(self, contact_key, impression, notes):
        message = "Impression saved"
        success = True

        c = tools.getKey(contact_key).get()
        c.create.impression(impression, notes)

        #Return message to confirm 
        return_vals = [success, message]
        return return_vals

    def newIndividual(self, name, team_key, email, password, admin):
        message = "<b>" + name + "</b> created"
        success = True

        s = tools.getSettingsKey(self).get()
        exists = s.exists.individual(email)

        if exists[0] == False:
            if email == "":
                email = None

            if team_key == "team":
                team_key = None

            s.create.individual(name, tools.getKey(team_key), email, password, admin)

        else:
            #If this email address already exists for a user
            message = "Sorry, but this email address is already being used."
            success = False

        #Return message to confirm 
        return_vals = [success, message]
        return return_vals

    def newTeam(self, name):
        message = "<b>" + name + "</b> created"
        success = True

        s = tools.getSettingsKey(self).get()
        s.create.team(name)

        #Return message to confirm 
        return_vals = [success, message]
        return return_vals

    def offlineDonation(self, name, email, amount_donated, notes, address, team_key, individual_key, add_deposit):
        message = "Offline donation created"
        success = True

        s = tools.getSettingsKey(self).get()

        if address == "":
            address = None
        else:
            address = json.loads(address)

        if team_key == "" or team_key == "general":
            team_key = None
        else:
            team_key = tools.getKey(team_key)

        if individual_key == "" or individual_key == None or individual_key == "none":
            individual_key = None
        else:
            individual_key = tools.getKey(individual_key)
            

        s.create.donation(name, email, amount_donated, amount_donated, address, team_key, individual_key, add_deposit, "", "", "offline", False, None)

        #Return message to confirm 
        return_vals = [success, message]
        return return_vals
    
    def updateDonation(self, donation_key, notes, team_key, individual_key, add_deposit):
        message = "Donation has been saved"
        success = True

        d = tools.getKey(donation_key).get()

        if team_key == "general":
            team_key = None
        elif team_key:
            team_key = tools.getKey(team_key)

        if individual_key:
            individual_key = tools.getKey(individual_key)

        d.update(notes, team_key, individual_key, add_deposit)

        #Return message to confirm 
        return_vals = [success, message]
        return return_vals

    def updateContact(self, contact_key, name, email, phone, notes, address):
        message = "Contact has been saved"
        success = True

        c = tools.getKey(contact_key).get()
        address = json.loads(address)
        c.update(name, email, phone, notes, address)
        
        #Return message to confirm 
        return_vals = [success, message]
        return return_vals

    def updateSettings(self, name, email, mc_use, mc_apikey, mc_donorlist, paypal_id, impressions, amount1, amount2, amount3, amount4, use_custom, confirmation_header, confirmation_info, confirmation_footer, confirmation_text, donor_report_text):
        message = "Settings have been updated"
        success = True

        s = tools.getSettingsKey(self).get()
        s.update(name, email, mc_use, mc_apikey, mc_donorlist, paypal_id, impressions, amount1, amount2, amount3, amount4, use_custom, confirmation_header, confirmation_info, confirmation_footer, confirmation_text, donor_report_text)

        #Return message to confirm 
        return_vals = [success, message]
        return return_vals

    def updateTeam(self, team_key, name, show_team):
        message = "Team has been updated"
        success = True

        t = tools.getKey(team_key).get()
        t.update(name, show_team)

        #Return message to confirm 
        return_vals = [success, message]
        return return_vals

#### ---- Contact merge ---- ####
    def mergeContacts(self, contact1, contact2):
        message = "Contacts merged"
        success = True

        c1 = tools.getKey(contact1)
        c2 = tools.getKey(contact2)

        tools.mergeContacts(c1, c2)

        #Return message to confirm 
        return_vals = [success, message]
        return return_vals

#### ---- Search ---- ####
    def getContactsJSON(self):
        s = tools.getSettingsKey(self).get()
        return s.data.contactsJSON

#### ---- Donation depositing ---- ####
    def depositDonations(self, donation_keys):
        message = "Donations deposited."
        success = True

        if donation_keys != []:
            s = tools.getSettingsKey(self).get()
            s.deposits.deposit(donation_keys)

        else:
            message = "No donations to deposit."
            success = False

        #Return message to confirm 
        return_vals = [success, message]
        return return_vals

    def removeFromDeposits(self, donation_keys):
        message = "Donations removed from deposits."
        success = True

        s = tools.getSettingsKey(self).get()

        donation_keys = tools.strArrayToKey(self, donation_keys)
        s.deposits.remove(donation_keys)

        #Return message to confirm 
        return_vals = [success, message]
        return return_vals

#### ---- Confirmation Letters ---- ####
    def emailReceipt(self, donation_key):
        message = "Email sent"
        success = True

        d = tools.getKey(donation_key).get()

        #Email receipt to donor
        d.review.archive()
        d.confirmation.task(60)

        #Return message to confirm
        return_vals = [success, message]
        return return_vals

    def printReceipt(self, donation_key):
        message = "Receipt open for printing"
        success = True

        d = tools.getKey(donation_key).get()

        #Print receipt to donor
        d.review.archive()
        print_url = d.confirmation.print_url(None)

        #Return message to confirm
        return_vals = [success, message, print_url]
        return return_vals

    def archiveDonation(self, donation_key):
        message = "Donation archived"
        success = True

        d = tools.getKey(donation_key).get()
        d.review.archive()

        #Return message to confirm
        return_vals = [success, message]
        return return_vals

    def emailAnnualReport(self, contact_key, year):
        message = "Annual report sent"
        success = True

        taskqueue.add(queue_name="annualreport", url="/tasks/annualreport", params={'contact_key' : contact_key, 'year' : year})

        #Return message to confirm
        return_vals = [success, message]
        return return_vals

#### ---- Data deletion ---- ####
    def deleteDonation(self, donation_key):
        message = "Donation deleted"
        success = True

        tools.getKey(donation_key).delete()

        #Return message to confirm
        return_vals = [success, message]
        return return_vals

    def deleteContact(self, contact_key):
        message = "Contact deleted"
        success = True

        tools.getKey(contact_key).delete()

        #Return message to confirm
        return_vals = [success, message]
        return return_vals

    def deleteTeam(self, team_key):
        message = "Team deleted"
        success = True

        tools.getKey(team_key).delete()

        #Return message to confirm
        return_vals = [success, message]
        return return_vals

    def semi_deleteIndividual(self, individual_key):
        message = "Individual deleted"
        success = True

        user_key = tools.getUserKey(self)
        
        i_key = tools.getKey(individual_key)
        isAdmin = user_key.get().admin

        if isAdmin == True:
            i_key.delete()
        else:
            if user_key == individual_key:
                i_key.delete()
            else:
                #Access denied - non-admin trying to delete someone else
                message = "Failed - Access denied"
                success = False

        #Return message to confirm 
        return_vals = [success, message]
        return return_vals