# coding: utf-8
import logging, json, datetime, appengine_config, webapp2
from google.appengine.api import taskqueue

import GlobalUtilities as tools
import DataModels as models

class RPCHandler(webapp2.RequestHandler):
    def __init__(self, request, response):
        self.initialize(request, response)
        self.methods = RPCMethods()

    def get(self):
        self.response.headers['Access-Control-Allow-Origin'] = '*'
        authenticated = tools.RPCcheckAuthentication(self, True)
        #authenticated = True

        func = None
        action = self.request.get('action')

        if action:
            logging.info("Action: " + str(action))

            if action[0] == '_':
                self.error(403) # access denied
                return

            elif action[0:4] == 'pub_':
                func = getattr(self.methods, action, None)

            elif action[0:5] == "semi_":
                if authenticated == "semi" or authenticated == True:
                    func = getattr(self.methods, action, None)
                else:
                    self.error(401)
                    self.response.out.write("I'm not authorized to give you that information until you log in. Sorry!")

            else:
                if authenticated == True:
                    func = getattr(self.methods, action, None)
                else:
                    self.error(401)
                    self.response.out.write("I'm not authorized to give you that information until you log in. Sorry!")


        if not func:
            self.error(404) # method not found
            return

        args = ()
        while True:
            key = 'arg%d' % len(args)
            val = self.request.get(key)
            if val:
                args += (json.loads(val),)
            else:
                break

        result = func(*args)
        dthandler = lambda obj: obj.isoformat() if isinstance(obj, datetime.datetime) else None
        self.response.out.write(json.dumps(result, default=dthandler))
    
    def post(self):
        self.response.headers['Access-Control-Allow-Origin'] = '*'
        authenticated = tools.RPCcheckAuthentication(self, True)

        args = json.loads(self.request.body)
        logging.info(args)
        
        func, args = args[0], args[1:]

        if func[0] == '_':
            self.error(403) # access denied
            return

        elif func[0:4] == "pub_":
            func = getattr(self.methods, func, None)

        elif func[0:5] == "semi_":
            if authenticated == "semi" or authenticated == True:
                func = getattr(self.methods, func, None)
            else:
                self.error(401)
                self.response.out.write("I'm not authorized to give you that information until you log in. Sorry!")

        else:
            if authenticated == True:
                func = getattr(self.methods, func, None)
            else:
                self.error(401)
                self.response.out.write("I'm not authorized to give you that information until you log in. Sorry!")

        if not func:
            self.error(404) # file not found
            return

        result = func(*args)
        self.response.out.write(json.dumps(result))
   
## -- Set of functions that returns data to above GET request -- ##
class RPCMethods:
    # Every function here gives a success/fail and a response.
    # Even though there's no response needed, we have to return
    # something so it integrates with other functions
    # that do have a value to return. The response in that case is None

#### ---- TEMPORARY TEST FUNCTIONS - SHOULD BE HIDDEN ON PRODUCTION RELEASE ---- ####

    def pub_sandboxSettings(self):
        name = "Testing"
        email = "tester@example.com"
        settings = tools.newSettings(self, name, email)

        return settings.urlsafe()

    def pub_refreshSandbox(self):
        #Local SDK
        settings = "agxkZXZ-Z2hpY2FsbHNyFgsSCFNldHRpbmdzGICAgICAgICAUAw"

        #GHI Calls sandbox
        settings = "agpzfmdoaWNhbGxzcg4LEghTZXR0aW5ncxgBDA"

        #Production
        # settings = "ag5zfmdoaWRvbmF0aW9uc3IQCxIIU2V0dGluZ3MY9dIWDA"

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

        tools.flushMemcache(self)
        return "Success"

#### ---- Globalhopeindia.org Utility Functions ---- ####
    def individualExists(self, email):
        settings = tools.getSettingsKey(self)
        return settings.get().exists.individual(email)

    def pub_allTeams(self, settings):
    # This returns a json list of teams
        s = tools.getKey(settings).get()

        all_teams = []
        for t in s.data.display_teams:
            team = [t.name, t.key.urlsafe()]           
            all_teams.append(team)
        
        return all_teams

    def pub_individualInfo(self, team_key, individual_key):
        i = tools.getKey(individual_key).get()
        t_key = tools.getKey(team_key)
        return i.data.info(t_key)

    def pub_teamInfo(self, team_key):
    # This returns a simplejson list of team members' names, hosted link to picture, and description
    # Response parsed by Javascript on main GHI site
        t = tools.getKey(team_key).get()
        return t.data.members_list

app = webapp2.WSGIApplication([
    ('/rpc', RPCHandler),
    ], debug=True)
app = appengine_config.recording_add_wsgi_middleware(app)