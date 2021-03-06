import appengine_config
import json
import logging
import uuid

import GlobalUtilities as tools
import spreadsheet_pipelines
from google.appengine.api import taskqueue, memcache
from google.appengine.ext import deferred

# Cloud Endpoints
import endpoints

from protorpc import remote
from endpoints_messages import *

## Cloud Endpoints Cookies - monkey patch
from endpoints import api_config


class PatchedApiConfigGenerator(api_config.ApiConfigGenerator):
    def pretty_print_config_to_json(self, services, hostname=None):
        json_string = super(PatchedApiConfigGenerator, self).pretty_print_config_to_json(
            services, hostname=hostname)
        to_patch = json.loads(json_string)
        to_patch['auth'] = {'allowCookieAuth': True}
        return json.dumps(to_patch, sort_keys=True, indent=2)


api_config.ApiConfigGenerator = PatchedApiConfigGenerator

## End monkey patch

endpoints_client_id = "AIzaSyB7k0LsUXibTJHkCx_D3MA0HT6tQAtYZAo"
endpoints_description = "GHI Donations API"
endpoints_clients = [endpoints_client_id, endpoints.API_EXPLORER_CLIENT_ID]


@endpoints.api(name='ghidonations', version='v1',
               description=endpoints_description,
               allowed_client_ids=endpoints_clients)
class EndpointsAPI(remote.Service):
    #### ---- Globalhopeindia.org Utility Functions ---- ####

    # public.all_teams
    @endpoints.method(AllTeams_In, AllTeams_Out, path='public/all_teams',
                      http_method='GET', name='public.all_teams')
    def public_all_teams(self, req):
        s = tools.getKey(req.settings_key).get()

        all_teams = []
        for t in s.data.display_teams:
            team = Team_Data(name=t.name, key=t.key.urlsafe())
            all_teams.append(team)

        return AllTeams_Out(objects=all_teams)

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
        isAdmin, s = tools.checkAuthentication(self, True, from_endpoints=True)

        if req.query == None:
            req.query = ""

        results = s.search.contact(req.query, query_cursor=req.query_cursor)
        logging.info("Getting contacts with query: " + req.query)

        contacts = []
        new_cursor = tools.getWebsafeCursor(results[1])

        for c in results[0]:
            f = c.fields
            contact = Contact_Data(key=f[0].value, name=f[1].value, email=tools.truncateEmail(f[2].value))
            contacts.append(contact)

        return Contacts_Out(objects=contacts, new_cursor=new_cursor)

    # get.contact_donations
    @endpoints.method(GetContactDonations_In, Donations_Out, path='get/contact_donations',
                      http_method='GET', name='get.contact_donations')
    def get_contact_donations(self, req):
        isAdmin, s = tools.checkAuthentication(self, True, from_endpoints=True)
        query = "contact_key:" + str(req.contact_key)

        results = s.search.donation(query, query_cursor=req.query_cursor)
        logging.info("Getting contact donations with query: " + query)

        donations = []
        new_cursor = tools.getWebsafeCursor(results[1])

        for d in results[0]:
            f = d.fields

            donation = Donation_Data(key=f[0].value, formatted_donation_date=f[9].value, name=f[2].value,
                                     email=tools.truncateEmail(f[3].value),
                                     payment_type=f[5].value, amount_donated=tools.moneyAmount(f[4].value))

            donations.append(donation)

        return Donations_Out(objects=donations, new_cursor=new_cursor)

    # get.deposits
    @endpoints.method(Query_In, Deposits_Out, path='get/deposits',
                      http_method='GET', name='get.deposits')
    def get_deposits(self, req):
        isAdmin, s = tools.checkAuthentication(self, True, from_endpoints=True)

        if req.query == None:
            req.query = ""

        results = s.search.deposit(req.query, query_cursor=req.query_cursor)
        logging.info("Getting deposits with query: " + req.query)

        deposits = []
        new_cursor = tools.getWebsafeCursor(results[1])

        for de in results[0]:
            f = de.fields

            deposit = Deposit_Data(key=f[0].value, time_deposited=f[1].value)
            deposits.append(deposit)

        return Deposits_Out(objects=deposits, new_cursor=new_cursor)

    # get.donations
    @endpoints.method(Query_In, Donations_Out, path='get/donations',
                      http_method='GET', name='get.donations')
    def get_donations(self, req):
        isAdmin, s = tools.checkAuthentication(self, True, from_endpoints=True)
        query = req.query

        if query == None:
            query = ""

        results = s.search.donation(query, query_cursor=req.query_cursor)
        logging.info("Getting donations with query: " + query)

        donations = []
        new_cursor = tools.getWebsafeCursor(results[1])

        for d in results[0]:
            f = d.fields

            team_name = f[6].value
            if not team_name:
                team_name = " "

            individual_name = f[7].value
            if not individual_name:
                individual_name = " "

            donation = Donation_Data(key=f[0].value, formatted_donation_date=f[9].value, name=f[2].value,
                                     email=tools.truncateEmail(f[3].value),
                                     payment_type=f[5].value, amount_donated=tools.moneyAmount(f[4].value),
                                     team_name=team_name, individual_name=individual_name)

            donations.append(donation)

        return Donations_Out(objects=donations, new_cursor=new_cursor)

    # get.individuals
    @endpoints.method(Query_In, Individuals_Out, path='get/individuals',
                      http_method='GET', name='get.individuals')
    def get_individuals(self, req):
        isAdmin, s = tools.checkAuthentication(self, True, from_endpoints=True)

        if req.query == None:
            req.query = ""

        results = s.search.individual(req.query, query_cursor=req.query_cursor)
        logging.info("Getting individuals with query: " + req.query)

        individuals = []
        new_cursor = tools.getWebsafeCursor(results[1])

        for i in results[0]:
            f = i.fields

            individual = Individual_Data(key=f[0].value, name=f[1].value, email=f[2].value,
                                         raised=tools.moneyAmount(f[4].value))
            individuals.append(individual)

        return Individuals_Out(objects=individuals, new_cursor=new_cursor)

    # get.monthly_chart_data
    @endpoints.method(NoRequestParams, JSON_Out, path='get/monthly_chart_data',
                      http_method='GET', name='get.monthly_chart_data')
    def monthly_chart_data(self, req):
        isAdmin, s = tools.checkAuthentication(self, True, from_endpoints=True)

        json_data = s.one_month_history

        return JSON_Out(json_data=json_data)

    # mailchimp.lists
    @endpoints.method(MailchimpLists_In, MailchimpLists_Out, path='mailchimp/lists',
                      http_method='GET', name='mailchimp.lists')
    def mailchimp_lists(self, req):
        isAdmin, s = tools.checkAuthentication(self, True, from_endpoints=True)

        response = tools.getMailchimpLists(self, req.mc_apikey)
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
    def get_teams(self, req):
        isAdmin, s = tools.checkAuthentication(self, True, from_endpoints=True)

        if req.query == None:
            req.query = ""

        results = s.search.team(req.query, query_cursor=req.query_cursor)
        logging.info("Getting teams with query: " + req.query)

        teams = []
        new_cursor = tools.getWebsafeCursor(results[1])

        for t in results[0]:
            f = t.fields

            team = Team_Data(key=f[0].value, name=f[1].value, donation_total=tools.moneyAmount(f[2].value))
            teams.append(team)

        return Teams_Out(objects=teams, new_cursor=new_cursor)

    # get.team_donation_total
    @endpoints.method(TeamKey_In, GetTeamDonationTotal_Out, path='get/team_donation_total',
                      http_method='GET', name='get.team_donation_total')
    def get_team_donation_total(self, req):
        isAdmin, s = tools.checkAuthentication(self, True, from_endpoints=True)

        t = tools.getKey(req.team_key).get()
        donation_total = tools.moneyAmount(t.data.donation_total)

        return GetTeamDonationTotal_Out(donation_total=donation_total)

    # get.team_members
    @endpoints.method(GetTeamMembers_In, Individuals_Out, path='get/team_members',
                      http_method='GET', name='get.team_members')
    def get_team_members(self, req):
        isAdmin, s = tools.checkAuthentication(self, True, from_endpoints=True)
        query = "team_key:" + str(req.team_key)

        results = s.search.individual(query, query_cursor=req.query_cursor)
        logging.info("Getting team members with query: " + query)

        individuals = []
        new_cursor = tools.getWebsafeCursor(results[1])

        for i in results[0]:
            f = i.fields

            individual = Individual_Data(key=f[0].value, name=f[1].value, email=f[2].value,
                                         raised=tools.moneyAmount(f[4].value))
            individuals.append(individual)

        return Individuals_Out(objects=individuals, new_cursor=new_cursor)

    # get.team_totals
    @endpoints.method(IndividualKey_In, GetTeamTotals_Out, path='get/team_totals',
                      http_method='GET', name='get.team_totals')
    def get_team_totals(self, req):
        s = tools.getSettingsKey(self, endpoints=True).get()

        i = tools.getKey(req.individual_key).get()

        team_totals = []
        for tl in i.teamlist_entities:
            total = GetTeamTotals_Data(team_name=tl.team_name, donation_total=tools.moneyAmount(tl.data.donation_total))
            team_totals.append(total)

        return GetTeamTotals_Out(team_totals=team_totals)

    # get.individual_donations
    @endpoints.method(GetIndividualDonations_In, Donations_Out, path='semi/get/individual_donations',
                      http_method='GET', name='semi.get.individual_donations')
    def semi_get_individual_donations(self, req):
        isAdmin, s = tools.checkAuthentication(self, False, from_endpoints=True)
        query = "individual_key:" + str(req.individual_key)

        results = s.search.donation(query, query_cursor=req.query_cursor)
        logging.info("Getting individual donations with query: " + query)

        donations = []
        new_cursor = tools.getWebsafeCursor(results[1])

        for d in results[0]:
            f = d.fields

            team_name = f[6].value
            if team_name == None:
                team_name = ""

            donation = Donation_Data(key=f[0].value, formatted_donation_date=f[9].value, name=f[2].value,
                                     email=tools.truncateEmail(f[3].value),
                                     payment_type=f[5].value, amount_donated=tools.moneyAmount(f[4].value),
                                     team_name=team_name)

            donations.append(donation)

        return Donations_Out(objects=donations, new_cursor=new_cursor)

    # semi.get.team_members
    @endpoints.method(SemiGetTeamMembers_In, SemiGetTeamMembers_Out, path='semi/get/team_members',
                      http_method='GET', name='semi.get.team_members')
    def semi_get_team_members(self, req):
        # Returns team information
        isAdmin, s = tools.checkAuthentication(self, False, from_endpoints=True)

        t = tools.getKey(req.team_key).get()
        members_list = t.data.members_list

        members = []
        for m in members_list:
            member = SemiGetTeamMembers_Data(key=m[2], name=m[0])
            members.append(member)

        return SemiGetTeamMembers_Out(objects=members)

    #### ---- Data creation/updating ---- ####
    # donation.mark_unreviewed
    @endpoints.method(DonationKey_In, SuccessMessage_Out, path='donation/mark_unreviewed',
                      http_method='POST', name='donation.mark_unreviewed')
    def donation_mark_unreviewed(self, req):
        message = "Donation marked as unreviewed"
        success = True

        isAdmin, s = tools.checkAuthentication(self, True, from_endpoints=True)

        d = tools.getKey(req.donation_key).get()
        d.review.markUnreviewed()

        return SuccessMessage_Out(success=success, message=message)

    # new.contact
    @endpoints.method(NewContact_In, SuccessMessage_Out, path='new/contact',
                      http_method='POST', name='new.contact')
    def new_contact(self, req):
        message = "<b>" + req.name + "</b> created"
        success = True

        isAdmin, s = tools.checkAuthentication(self, True, from_endpoints=True)
        contact_exists = s.exists.contact(email=req.email)

        address = [req.address.street, req.address.city, req.address.state, req.address.zipcode]

        if contact_exists[0] == False:
            s.create.contact(req.name, email=req.email, phone=req.phone, address=address, notes=req.notes, add_mc=True)

        else:
            # If this email address already exists for a user
            message = "Whoops! You entered an email address already in use by another contact."
            success = False

        return SuccessMessage_Out(success=success, message=message)

    # new.impression
    @endpoints.method(NewImpression_In, SuccessMessage_Out, path='new/impression',
                      http_method='POST', name='new.impression')
    def new_impression(self, req):
        message = "Impression saved"
        success = True

        isAdmin, s = tools.checkAuthentication(self, True, from_endpoints=True)

        c = tools.getKey(req.contact_key).get()
        c.create.impression(req.impression, req.notes)

        return SuccessMessage_Out(success=success, message=message)

    # new.individual
    @endpoints.method(NewIndividual_In, SuccessMessage_Out, path='new/individual',
                      http_method='POST', name='new.individual')
    def new_individual(self, req):
        message = "<b>" + req.name + "</b> created"
        success = True

        isAdmin, s = tools.checkAuthentication(self, True, from_endpoints=True)
        exists = s.exists.individual(req.email)

        email, team_key = req.email, req.team_key

        if email == "": email = None
        if team_key == "team": team_key = None

        if email == None or exists[0] == False:
            s.create.individual(req.name, tools.getKey(team_key), email, req.password, admin=req.admin)

        else:
            # If this email address already exists for a user
            message = "Sorry, but this email address is already being used."
            success = False

        return SuccessMessage_Out(success=success, message=message)

    # new.team
    @endpoints.method(NewTeam_In, SuccessMessage_Out, path='new/team',
                      http_method='POST', name='new.team')
    def new_team(self, req):
        message = "<b>" + req.name + "</b> created"
        success = True

        isAdmin, s = tools.checkAuthentication(self, True, from_endpoints=True)
        s.create.team(req.name)

        return SuccessMessage_Out(success=success, message=message)

    # new.offline_donation
    @endpoints.method(NewOfflineDonation_In, SuccessMessage_Out, path='new/offline_donation',
                      http_method='POST', name='new.offline_donation')
    def new_offline_donation(self, req):
        message = "Offline donation created"
        success = True

        isAdmin, s = tools.checkAuthentication(self, True, from_endpoints=True)

        # Make req variables local
        name, email, amount_donated, notes, address, team_key, individual_key, \
        add_deposit = req.name, req.email, tools.toDecimal(req.amount_donated), req.notes, \
                      req.address, req.team_key, req.individual_key, req.add_deposit

        # Check for null value in individual field
        if individual_key == "none":
            individual_key = None

        if address:
            address = [address.street, address.city, address.state, address.zipcode]

        if team_key:
            team_key = tools.getKey(team_key)

        if individual_key:
            individual_key = tools.getKey(individual_key)

        s.create.donation(name, email, amount_donated, "offline", address=address, team_key=team_key,
                          individual_key=individual_key, add_deposit=add_deposit, special_notes=notes)

        return SuccessMessage_Out(success=success, message=message)

    # update.donation
    @endpoints.method(UpdateDonation_In, SuccessMessage_Out, path='update/donation',
                      http_method='POST', name='update.donation')
    def update_donation(self, req):
        message = "Donation has been saved"
        success = True

        isAdmin, s = tools.checkAuthentication(self, True, from_endpoints=True)

        d = tools.getKey(req.donation_key).get()

        # Make req variables local
        team_key, individual_key = req.team_key, req.individual_key

        if team_key:
            if team_key == "general":
                team_key = None
            else:
                team_key = tools.getKey(team_key)

        if individual_key:
            individual_key = tools.getKey(individual_key)

        d.update(req.notes, team_key, individual_key, None, req.donation_date)

        return SuccessMessage_Out(success=success, message=message)

    # update.contact
    @endpoints.method(UpdateContact_In, SuccessMessage_Out, path='update/contact',
                      http_method='POST', name='update.contact')
    def update_contact(self, req):
        message = "Contact has been saved"
        success = True

        isAdmin, s = tools.checkAuthentication(self, True, from_endpoints=True)

        c = tools.getKey(req.contact_key).get()

        a = req.address
        address = [a.street, a.city, a.state, a.zipcode]

        # Check to see if a new email was added and see if it already exists
        list_diff = tools.listDiff(c.email, req.email)

        if list_diff:
            email_exists = s.exists.contact(email=list_diff)[0]
        else:
            email_exists = False

        if email_exists == True:
            success = False
            message = "Whoops! You entered an email address already in use by another contact."
        else:
            c.update(req.name, req.email, req.phone, req.notes, address)

        return SuccessMessage_Out(success=success, message=message)

    # update.settings
    @endpoints.method(UpdateSettings_In, SuccessMessage_Out, path='update/settings',
                      http_method='POST', name='update.settings')
    def update_settings(self, req):
        message = "Settings have been updated"
        success = True

        isAdmin, s = tools.checkAuthentication(self, True, from_endpoints=True)

        s.update(req.name, req.email, req.mc_use, req.mc_apikey, req.mc_donorlist,
                 req.paypal_id, req.impressions, req.donate_parent, req.amount1, req.amount2, req.amount3,
                 req.amount4, req.use_custom, req.confirmation_header, req.confirmation_info,
                 req.confirmation_footer, req.confirmation_text, req.donor_report_text)

        return SuccessMessage_Out(success=success, message=message)

    # update.team
    @endpoints.method(UpdateTeam_In, SuccessMessage_Out, path='update/team',
                      http_method='POST', name='update.team')
    def update_team(self, req):
        message = "Team has been updated"
        success = True

        isAdmin, s = tools.checkAuthentication(self, True, from_endpoints=True)

        t = tools.getKey(req.team_key).get()
        t.update(req.name, req.show_team)

        return SuccessMessage_Out(success=success, message=message)

    #### ---- Contact merge ---- ####
    # merge.contacts
    @endpoints.method(MergeContacts_In, SuccessMessage_Out, path='merge/contacts',
                      http_method='POST', name='merge.contacts')
    def merge_contacts(self, req):
        message = "Contacts merged"
        success = True

        isAdmin, s = tools.checkAuthentication(self, True, from_endpoints=True)

        c1 = tools.getKey(req.contact1)
        c2 = tools.getKey(req.contact2)

        tools.mergeContacts(c1, c2)

        return SuccessMessage_Out(success=success, message=message)

    #### ---- Search ---- ####
    # get.contacts_json
    @endpoints.method(NoRequestParams, JSON_Out, path='get/contacts_json',
                      http_method='GET', name='get.contacts_json')
    def get_contacts_json(self, req):
        isAdmin, s = tools.checkAuthentication(self, True, from_endpoints=True)

        return JSON_Out(json_data=s.data.contactsJSON)

    #### ---- Donation depositing ---- ####
    # deposits.add
    @endpoints.method(Deposits_In, SuccessMessage_Out, path='deposits/add',
                      http_method='POST', name='deposits.add')
    def deposits_add(self, req):
        message = "Donations deposited."
        success = True

        isAdmin, s = tools.checkAuthentication(self, True, from_endpoints=True)

        if req.donation_keys != []:
            donation_keys = []
            for k in req.donation_keys:
                donation_keys.append(str(k))

            deferred.defer(s.deposits.deposit, donation_keys, _queue="backend")

        else:
            message = "No donations to deposit."
            success = False

        return SuccessMessage_Out(success=success, message=message)

    # deposits.remove
    @endpoints.method(Deposits_In, SuccessMessage_Out, path='deposits/remove',
                      http_method='POST', name='deposits.remove')
    def deposits_remove(self, req):
        message = "Donations removed from deposits."
        success = True

        isAdmin, s = tools.checkAuthentication(self, True, from_endpoints=True)

        if req.donation_keys != []:
            donation_keys = []
            for k in req.donation_keys:
                donation_keys.append(str(k))

            deferred.defer(s.deposits.remove, donation_keys, _queue="backend")

        return SuccessMessage_Out(success=success, message=message)

    #### ---- Confirmation Letters ---- ####

    # confirmation.email
    @endpoints.method(DonationKey_In, SuccessMessage_Out, path='confirmation/email',
                      http_method='POST', name='confirmation.email')
    def confirmation_email(self, req):
        message = "Email sent"
        success = True

        isAdmin, s = tools.checkAuthentication(self, True, from_endpoints=True)

        d = tools.getKey(req.donation_key).get()

        if not d.email or d.email == ['']:
            success = False
            message = "Email not sent. Contact doesn't have an email address."

        else:
            # Email receipt to donor
            d.review.archive()
            d.confirmation.task(60)

        return SuccessMessage_Out(success=success, message=message)

    # confirmation.print
    @endpoints.method(DonationKey_In, ConfirmationPrint_Out, path='confirmation/print',
                      http_method='POST', name='confirmation.print')
    def printReceipt(self, req):
        message = "Receipt open for printing"
        success = True

        isAdmin, s = tools.checkAuthentication(self, True, from_endpoints=True)
        d = tools.getKey(req.donation_key).get()

        # Print receipt to donor
        d.review.archive()
        print_url = d.confirmation.print_url(None)

        return ConfirmationPrint_Out(success=success, message=message, print_url=print_url)

    # confirmation.annual_report
    @endpoints.method(ConfirmationAnnualReport_In, SuccessMessage_Out, path='confirmation/annual_report',
                      http_method='POST', name='confirmation.annual_report')
    def confirmation_annual_report(self, req):
        message = "Annual report sent"
        success = True

        isAdmin, s = tools.checkAuthentication(self, True, from_endpoints=True)

        taskqueue.add(queue_name="annualreport", url="/tasks/annualreport",
                      params={'contact_key': req.contact_key, 'year': req.year})

        return SuccessMessage_Out(success=success, message=message)

    # donation.archive
    @endpoints.method(DonationKey_In, SuccessMessage_Out, path='donation/archive',
                      http_method='POST', name='donation.archive')
    def donation_archive(self, req):
        message = "Donation archived"
        success = True

        isAdmin, s = tools.checkAuthentication(self, True, from_endpoints=True)

        d = tools.getKey(req.donation_key).get()
        d.review.archive()

        return SuccessMessage_Out(success=success, message=message)

    # donation.delete
    @endpoints.method(DonationKey_In, SuccessMessage_Out, path='donation/delete',
                      http_method='POST', name='donation.delete')
    def donation_delete(self, req):
        message = "Donation deleted"
        success = True

        isAdmin, s = tools.checkAuthentication(self, True, from_endpoints=True)

        tools.getKey(req.donation_key).delete()

        return SuccessMessage_Out(success=success, message=message)

    # contact.delete
    @endpoints.method(ContactKey_In, SuccessMessage_Out, path='contact/delete',
                      http_method='POST', name='contact.delete')
    def contact_delete(self, req):
        message = "Contact deleted"
        success = True

        isAdmin, s = tools.checkAuthentication(self, True, from_endpoints=True)

        tools.getKey(req.contact_key).delete()

        return SuccessMessage_Out(success=success, message=message)

    # contact.info
    @endpoints.method(ContactKey_In, Contact_Info, path='contact/info',
                      http_method='POST', name='contact.info')
    def contact_info(self, req):
        isAdmin, s = tools.checkAuthentication(self, True, from_endpoints=True)
        c = tools.getKey(req.contact_key).get()

        return Contact_Info(key=c.websafe, name=c.name, email=c.email,
                            address=c.address)

    # team.delete
    @endpoints.method(TeamKey_In, SuccessMessage_Out, path='team/delete',
                      http_method='POST', name='team.delete')
    def deleteTeam(self, req):
        message = "Team deleted"
        success = True

        isAdmin, s = tools.checkAuthentication(self, True, from_endpoints=True)

        tools.getKey(req.team_key).delete()

        return SuccessMessage_Out(success=success, message=message)

    # individual.delete
    @endpoints.method(IndividualKey_In, SuccessMessage_Out, path='individual/delete',
                      http_method='POST', name='individual.delete')
    def individual_delete(self, req):
        message = "Individual deleted"
        success = True

        isAdmin, s = tools.checkAuthentication(self, True, from_endpoints=True)

        user_key = tools.getUserKey(self)
        isAdmin = user_key.get().admin

        i_key = tools.getKey(req.individual_key)

        if isAdmin == True:
            i_key.delete()
        else:
            if user_key == individual_key:
                i_key.delete()
            else:
                # Access denied - non-admin trying to delete someone else
                message = "Failed - Access denied"
                success = False

        return SuccessMessage_Out(success=success, message=message)

    #### ---- Spreadsheet Export Controllers ---- ####

    # spreadsheet.start
    @endpoints.method(SpreadsheetStart_In, SpreadsheetStart_Out, path='spreadsheet/start',
                      http_method='POST', name='spreadsheet.start')
    def spreadsheet_start(self, req):
        isAdmin, s = tools.checkAuthentication(self, True, from_endpoints=True)

        if req.mode not in ["contacts", "donations", "individuals"]:
            raise endpoints.NotFoundException("Incorrect spreadsheet mode")

        # Create unique identifier for this job
        job_id = str(uuid.uuid4())
        memcache.set(job_id, 0)

        stage = spreadsheet_pipelines.GenerateReport(s.websafe, req.mode, job_id)
        stage.start(queue_name='spreadsheet')

        pipeline_id = stage.pipeline_id
        memcache.set("id" + job_id, pipeline_id)

        return SpreadsheetStart_Out(job_id=job_id)

    # spreadsheet.check
    @endpoints.method(SpreadsheetCheck_In, SpreadsheetCheck_Out, path='spreadsheet/check',
                      http_method='POST', name='spreadsheet.check')
    def spreadsheet_check(self, req):
        isAdmin, s = tools.checkAuthentication(self, True, from_endpoints=True)

        completed, gcs_file_key = tools.checkTaskCompletion(s, req.job_id)
        status = tools.pipelineStatus(req.job_id)

        if completed:
            download_url = "http://commondatastorage.googleapis.com/" + gcs_file_key[1:]
        else:
            download_url = None

        return SpreadsheetCheck_Out(completed=completed, download_url=download_url, status=status)


app = endpoints.api_server([EndpointsAPI], restricted=False)
app = appengine_config.webapp_add_wsgi_middleware(app)
