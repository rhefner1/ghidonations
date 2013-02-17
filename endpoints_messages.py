from protorpc import messages

# public.all_teams
class AllTeamsIn(messages.Message):
    settings_key = messages.StringField(1, required=True)

class AllTeamsTeam(messages.Message):
	name = messages.StringField(1, required=True)
	key = messages.StringField(2, required=True)

class AllTeamsOut(messages.Message):
	all_teams = messages.MessageField(AllTeamsTeam, 1, repeated=True, required=True)