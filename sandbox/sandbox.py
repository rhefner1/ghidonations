import json, random, itertools
import GlobalUtilities as tools

### --- Execute this first --- ###
def createTestSandbox():
	name = "Testing"
	email = "tester@example.com"
	s = tools.newSettings(name, email)

	return s

###  --- Sandbox --- ###
def populateTestSandbox(settings_key=None, num_teams=13, num_individuals=500, num_contacts=2500):
	if not settings_key:
		settings_key = createTestSandbox()
		s = settings_key.get()

	else:
		s = settings_key.get()
		# Clearing out existing data

		for i in s.data.all_individuals:
		    i.key.delete()
		for t in s.data.all_teams:
		    t.key.delete()
		for d in s.data.all_deposits:
		    d.key.delete()
		for c in s.data.all_contacts:
		    for i in c.data.all_impressions:
		        i.key.delete()
		    c.key.delete()
		for d in s.data.all_donations:
		    d.key.delete()


	# Reset default settings values
	s.name = "Testing"
	s.email = "test@example.com"
	s.mc_use = False
	s.mc_apikey = None
	s.mc_donorlist = None
	s.impressions = []
	s.paypal_id = "test@example.com"
	s.amount1 = 25
	s.amount2 = 50
	s.amount3 = 75
	s.amount4 = 100
	s.use_custom = True
	s.confirmation_text = ""
	s.confirmation_info = ""
	s.confirmation_header = ""
	s.confirmation_footer = ""
	s.wp_url = None
	s.wp_username = None
	s.wp_password = None

	s.put()


	# Importing test data
	import contact_names, individual_names, team_names

	# Creating new data
	team_keys = []
	for t in itertools.islice(team_names.names, 0, num_teams):
		key = s.create.team( t["TeamName"] )
		team_keys.append(key)

	individual_keys = []
	for i in itertools.islice(individual_names.names, 0, num_individuals):
		team_key = team_keys[ random.randint(0, len(team_keys)-1 ) ]

		key = s.create.individual( i["GivenName"] + " " + i["Surname"], team_key, i["EmailAddress"], "password", True)
		individual_keys.append(key)

	for c in itertools.islice(contact_names.names, 0, num_contacts):
		phone = c["TelephoneNumber"].replace("-", "")
		address = json.dumps( [ c["StreetAddress"], c["City"], c["State"], c["ZipCode"] ] )
		s.create.contact( c["GivenName"] + " " + c["Surname"], c["EmailAddress"], phone, address, None, False)

		# Choose how many donations this contact should have
		for i in range(0,12):

			# Choose this donation's type
			if random.randint(0,1) == 0:
				payment_type = "offline"
			else:
				payment_type = "one-time"

			# Choose if this donations should have a designation
			if random.randint(0,1) == 1: 
				try:
					individual_key = individual_keys [ random.randint( 0, len(individual_keys)-1 ) ]
					team_key = individual_key.get().data.teams.fetch(1)[0].key

				except:
					team_key = None
					individual_key = None

			else:
				team_key = None
				individual_key = None

			# Choose the value of this donation
			confirmation_amount = float(random.randint(1000, 1000000)) / 100

			# If PayPal, take away 2.2%
			if payment_type == "offline":
				amount_donated = confirmation_amount
			else:
				amount_donated = confirmation_amount - confirmation_amount * .022

			s.create.donation( c["GivenName"] + " " + c["Surname"], c["EmailAddress"], str(amount_donated), str(confirmation_amount), None, team_key, individual_key, True, None, None, payment_type, False, None)

	taskqueue.add(url="/tasks/updateanalytics", params={}, queue_name="backend")
	tools.flushMemcache(self)