from protorpc import messages

### Common entity definitions
class Contact_Data(messages.Message):
    key = messages.StringField(1, required=True)
    name = messages.StringField(2, required=True)
    email = messages.StringField(3, required=True)

class Contacts_Out(messages.Message):
    objects = messages.MessageField(Contact_Data, 1, repeated=True)
    new_cursor = messages.StringField(2)

class Date_Data(messages.Message):
    day = messages.IntegerField(1, required=True)
    month = messages.IntegerField(2, required=True)
    year = messages.IntegerField(3, required=True)

class Deposit_Data(messages.Message):
    key = messages.StringField(1, required=True)
    time_deposited = messages.StringField(2, required=True)

class Deposits_Out(messages.Message):
    objects = messages.MessageField(Deposit_Data, 1, repeated=True)
    new_cursor = messages.StringField(2)

class Donation_Data(messages.Message):
    key = messages.StringField(1, required=True)
    formatted_donation_date = messages.StringField(2, required=True)
    name = messages.StringField(3, required=True)
    email = messages.StringField(4, required=True)
    payment_type = messages.StringField(5, required=True)
    amount_donated = messages.StringField(6, required=True)
    team_name = messages.StringField(7)

class Donations_Out(messages.Message):
    objects = messages.MessageField(Donation_Data, 1, repeated=True)
    new_cursor = messages.StringField(2)

class Individual_Data(messages.Message):
    key = messages.StringField(1, required=True)
    name = messages.StringField(2, required=True)
    email = messages.StringField(3, required=True)
    raised = messages.StringField(4, required=True)

class Individuals_Out(messages.Message):
    objects = messages.MessageField(Individual_Data, 1, repeated=True)
    new_cursor = messages.StringField(2)

class Team_Data(messages.Message):
    name = messages.StringField(1, required=True)
    key = messages.StringField(2, required=True)
    donation_total = messages.StringField(3, required=True)

class Teams_Out(messages.Message):
    objects = messages.MessageField(Team_Data, 1, repeated=True)
    new_cursor = messages.StringField(2)

class Query_In(messages.Message):
    query_cursor = messages.StringField(1)
    query = messages.StringField(2)

class SuccessMessage_Out(messages.Message):
    success = messages.BooleanField(1, required=True)
    message = messages.StringField(2, required=True)

### Single key arguments
class ContactKey_In(messages.Message):
    contact_key = messages.StringField(1, required=True)

class DonationKey_In(messages.Message):
    donation_key = messages.StringField(1, required=True)

class IndividualKey_In(messages.Message):
    individual_key = messages.StringField(1, required=True)

class TeamKey_In(messages.Message):
    team_key = messages.StringField(1, required=True)

### Method specific classes
# public.all_teams
class AllTeams_In(messages.Message):
    settings_key = messages.StringField(1, required=True)

class AllTeams_Out(messages.Message):
	objects = messages.MessageField(Team_Data, 1, repeated=True)
    
# public.individual_info
class IndividualInfo_In(messages.Message):
    team_key = messages.StringField(1, required=True)
    individual_key = messages.StringField(2, required=True)
    
class IndividualInfo_Out(messages.Message):
    image_url = messages.StringField(1, required=True)
    name = messages.StringField(2, required=True)
    description = messages.StringField(3, required=True)
    percentage = messages.IntegerField(4, required=True)
    message = messages.StringField(5, required=True)
    
# public.team_info
class TeamInfo_In(messages.Message):
    team_key = messages.StringField(1, required=True)
    
class TeamInfo_Data(messages.Message):
    name = messages.StringField(1, required=True)
    photo_url = messages.StringField(2, required=True)
    tl_key = messages.StringField(3, required=True)
    
class TeamInfo_Out(messages.Message):
    info_list = messages.MessageField(TeamInfo_Data, 1, repeated=True)

# get.contact_donations
class GetContactDonations_In(messages.Message):
    query_cursor = messages.StringField(1)
    contact_key = messages.StringField(2, required=True)

# mailchimp.lists
class MailchimpLists_In(messages.Message):
    mc_apikey = messages.StringField(1, required=True)

class MailchimpLists_Out(messages.Message):
    success = messages.BooleanField(1, required=True)
    mc_lists = messages.StringField(2, required=True)

    error_message = messages.StringField(3)

# get.team_members
class GetTeamMembers_In(messages.Message):
    query_cursor = messages.StringField(1)
    team_key = messages.StringField(2, required=True)

# semi.get.individual_donations
class GetIndividualDonations_In(messages.Message):
    query_cursor = messages.StringField(1)
    individual_key = messages.StringField(2, required=True)

# semi.get.team_members
class SemiGetTeamMembers_In(messages.Message):
    team_key = messages.StringField(1, required=True)

class SemiGetTeamMembers_Data(messages.Message):
    key = messages.StringField(1, required=True)
    name = messages.StringField(2, required=True)

class SemiGetTeamMembers_Out(messages.Message):
    objects = messages.MessageField(SemiGetTeamMembers_Data, 1, repeated=True)

# new.contact
class AddressInfo(messages.Message):
    street = messages.StringField(1, required=True)
    city = messages.StringField(2, required=True)
    state = messages.StringField(3, required=True)
    zipcode = messages.StringField(4, required=True)

class NewContact_In(messages.Message):
    name = messages.StringField(1, required=True)
    email = messages.StringField(2, required=True)
    phone = messages.StringField(3, required=True)
    address = messages.MessageField(AddressInfo, 4, required=True)
    notes = messages.StringField(5, required=True)

# new.impression
class NewImpression_In(messages.Message):
    contact_key = messages.StringField(1, required=True)
    impression = messages.StringField(2, required=True)
    notes = messages.StringField(3, required=True)

# new.indvidual
class NewIndividual_In(messages.Message):
    name = messages.StringField(1, required=True)
    team_key = messages.StringField(2, required=True)
    email = messages.StringField(3, required=True)
    password = messages.StringField(4, required=True)
    admin = messages.BooleanField(5, required=True)

# new.team
class NewTeam_In(messages.Message):
    name = messages.StringField(1, required=True)

# new.offline_donation
class NewOfflineDonation_In(messages.Message):
    name = messages.StringField(1, required=True)
    email = messages.StringField(2)
    amount_donated = messages.StringField(3, required=True)
    notes = messages.StringField(4)
    address = messages.MessageField(AddressInfo, 5)
    team_key = messages.StringField(6)
    individual_key = messages.StringField(7)
    add_deposit = messages.BooleanField(8, required=True)

# update.donation
class UpdateDonation_In(messages.Message):
    donation_key = messages.StringField(1, required=True)
    notes = messages.StringField(2, required=True)
    team_key = messages.StringField(3)
    individual_key = messages.StringField(4)
    add_deposit = messages.BooleanField(5, required=True)
    donation_date = messages.MessageField(Date_Data, 6)

# update.contact
class UpdateContact_In(messages.Message):
    contact_key = messages.StringField(1, required=True)
    name = messages.StringField(2, required=True)
    email = messages.StringField(3, required=True)
    phone = messages.StringField(4, required=True)
    notes = messages.StringField(5, required=True)
    address = messages.MessageField(AddressInfo, 6, required=True)

# update.settings
class UpdateSettings_In(messages.Message):
    name = messages.StringField(1, required=True)
    email = messages.StringField(2, required=True)
    mc_use = messages.BooleanField(3, required=True)
    mc_apikey = messages.StringField(4)
    mc_donorlist = messages.StringField(5)
    paypal_id = messages.StringField(6, required=True)
    impressions = messages.StringField(7, repeated=True)
    amount1 = messages.IntegerField(8, required=True)
    amount2 = messages.IntegerField(9, required=True)
    amount3 = messages.IntegerField(10, required=True)
    amount4 = messages.IntegerField(11, required=True)
    use_custom = messages.BooleanField(12, required=True)
    confirmation_header = messages.StringField(13, required=True)
    confirmation_info = messages.StringField(14, required=True)
    confirmation_footer = messages.StringField(15, required=True)
    confirmation_text = messages.StringField(16, required=True)
    donor_report_text = messages.StringField(17, required=True)

# update.team
class UpdateTeam_In(messages.Message):
    team_key = messages.StringField(1, required=True)
    name = messages.StringField(2, required=True)
    show_team = messages.BooleanField(3, required=True)

# merge.contacts
class MergeContacts_In(messages.Message):
    contact1 = messages.StringField(1, required=True)
    contact2 = messages.StringField(2, required=True)

# get.contacts_json
class NoRequestParams(messages.Message):
    pass

class JSON_Out(messages.Message):
    json_data = messages.StringField(1, required=True)

# get.team_totals
class GetTeamTotals_Data(messages.Message):
    team_name = messages.StringField(1, required=True)
    donation_total = messages.StringField(2, required=True)

class GetTeamTotals_Out(messages.Message):
    team_totals = messages.MessageField(GetTeamTotals_Data, 1, repeated=True)

# deposit_donations
class Deposits_In(messages.Message):
    donation_keys = messages.StringField(1, repeated=True)

# confirmation.print
class ConfirmationPrint_Out(messages.Message):
    success = messages.BooleanField(1, required=True)
    message = messages.StringField(2, required=True)
    print_url = messages.StringField(3, required=True)

# confirmation.annual_report
class ConfirmationAnnualReport_In(messages.Message):
    contact_key = messages.StringField(1, required=True)
    year = messages.IntegerField(2, required=True)

# spreadsheet.start
class SpreadsheetStart_In(messages.Message):
    mode = messages.StringField(1, required=True)
    filename = messages.StringField(2, required=True)
    query = messages.StringField(3, required=True)

class SpreadsheetStart_Out(messages.Message):
    job_id = messages.StringField(1, required=True)

# spreadsheet.check
class SpreadsheetCheck_In(messages.Message):
    job_id = messages.StringField(1, required=True)

class SpreadsheetCheck_Out(messages.Message):
    completed = messages.BooleanField(1, required=True)
    blob_key = messages.StringField(2)
