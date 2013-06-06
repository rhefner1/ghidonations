### --- Execute this first --- ###
name = "Testing"
email = "tester@example.com"
settings = tools.newSettings(self, name, email)

return settings.urlsafe()

###  --- Sandbox --- ###
settings = "ahBkZXZ-Z2hpZG9uYXRpb25zchYLEghTZXR0aW5ncxiAgICAgICAgFAM"

s = tools.getKey(settings).get()

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

team_key = s.create.team("Cool Group")

s.create.individual("Tester", team_key, "test@example.com", "ghi", True)
s.create.individual("Ryan Hefner", team_key, "rhefner1@gmail.com", "ghi", True)

s.create.contact("Sandra Baker", "sbaker@example.com", "9199858383", None, "Sandra is great!", False)
s.create.contact("James Bonner", "jbonner@example.com", "9195682254", None, None, False)
s.create.contact("James Winchester", "jwinchester@example.com", None, None, None, False)
s.create.contact("Clayton Joslin", "cjoslin@example.com", None, None, None, False)
s.create.contact("Robert Roberson", "rroberson@example.com", None, None, None, False)
s.create.contact("Thomas Dodge", "tdodge@example.com", None, None, None, False)
s.create.contact("Colleen Molina", "cmolina@example.com", None, None, None, False)
s.create.contact("Rachel Sanders", "rsanders@example.com", None, None, None, False)
s.create.contact("Jason Tinsley", "jtinsley@example.com", None, None, None, False)
s.create.contact("Christopher Walker", "cwalker@example.com", None, None, None, False)
s.create.contact("Evelyn Newsome", "enewsome@example.com", None, None, None, False)
s.create.contact("Jenny McGinty", "jmcginty@example.com", None, None, None, False)
s.create.contact("Sara Ruiz", "sruiz@example.com", None, None, None, False)
s.create.contact("Curtis Smalls", "csmalls@example.com", None, None, None, False)
s.create.contact("Constance Weekley", "cweekley@example.com", None, None, None, False)

s.create.donation("Sandra Baker", "sbaker@example.com", "12.34", "12.34", None, None, None, True, None, None, "offline", False, None)
s.create.donation("Sandra Baker", "sbaker@example.com", "1425.25", "1425.25", None, None, None, True, None, None, "offline", False, None)
s.create.donation("Sandra Baker", "sbaker@example.com", "2346.52", "2346.52", None, None, None, True, None, None, "offline", True, None)
s.create.donation("Colleen Molina", "cmolina@example.com", "27.50", "27.50", None, None, None, True, None, None, "offline", False, None)
s.create.donation("Colleen Molina", "cmolina@example.com", "77.50", "77.50", None, None, None, True, None, None, "offline", False, None)
s.create.donation("Sara Ruiz", "sruiz@example.com", "500.00", "500.00", None, None, None, True, None, None, "offline", False, None)
s.create.donation("Sara Ruiz", "sruiz@example.com", "700.00", "700.00", None, None, None, True, None, None, "offline", False, None)
s.create.donation("Constance Weekley", "cweekley@example.com", "1000.00", "1000.00", None, None, None, True, None, None, "offline", False, None)
s.create.donation("Constance Weekley", "cweekley@example.com", "6000.00", "6000.00", None, None, None, True, None, None, "offline", False, None)

taskqueue.add(url="/tasks/updateanalytics", params={}, queue_name="backend")

tools.flushMemcache(self)