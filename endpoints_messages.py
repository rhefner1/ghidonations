from protorpc import messages

# Common entity definitions
class Contact_Data(messages.Message):
    key = messages.StringField(1, required=True)
    name = messages.StringField(2, required=True)
    email = messages.StringField(3, required=True)

class Contacts_Out(messages.Message):
    contacts = messages.MessageField(Contact_Data, 1, repeated=True)
    new_cursor = messages.StringField(2, required=True)

class Deposit_Data(messages.Message):
    key = messages.StringField(1, required=True)
    time_deposited = messages.StringField(2, required=True)

class Deposits_Out(messages.Message):
    deposits = messages.MessageField(Deposit_Data, 1, repeated=True)
    new_cursor = messages.StringField(2, required=True)

class Donation_Data(messages.Message):
    key = messages.StringField(1, required=True)
    formatted_donation_date = messages.StringField(2, required=True)
    name = messages.StringField(3, required=True)
    email = messages.StringField(4, required=True)
    payment_type = messages.StringField(5, required=True)
    amount_donated = messages.StringField(6, required=True)

class Donations_Out(messages.Message):
    donations = messages.MessageField(Donation_Data, 1, repeated=True)
    new_cursor = messages.StringField(2, required=True)

class Individual_Data(messages.Message):
    key = messages.StringField(1, required=True)
    name = messages.StringField(2, required=True)
    email = messages.StringField(3, required=True)

class Individual_Out(messages.Message):
    individuals = messages.MessageField(Individual_Data, 1, repeated=True)
    new_cursor = messages.StringField(2, required=True)

class Team_Data(messages.Message):
    name = messages.StringField(1, required=True)
    key = messages.StringField(2, required=True)

class Teams_Out(messages.Message):
    teams = messages.MessageField(Team_Data, 1, repeated=True)
    new_cursor = messages.StringField(2, required=True)

class Query_In(messages.Message):
    query_cursor = messages.StringField(1, required=True)
    query = messages.StringField(2, required=True)

# public.all_teams
class AllTeams_In(messages.Message):
    settings_key = messages.StringField(1, required=True)

class AllTeams_Out(messages.Message):
	all_teams = messages.MessageField(TeamData, 1, repeated=True)
    
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
    info_list = messages.MessageField(TeamInfoData, 1, repeated=True)

# get.contact_donations
class GetContactDonations_In(messages.Message):
    query_cursor = messages.StringField(1, required=True)
    contact_key = messages.StringField(2, required=True)

# mailchimp.lists
class MailchimpLists_In(messages.Message):
    mc_apikey = messages.StringField(1, required=True)

class MailchimpLists_Out(messages.Message):
    success = messages.BooleanField(1, required=True)
    mc_lists = messages.StringField(2, required=True)

    error_message = messages.StringField(3)