import datetime
import json
import logging

import webapp2

import appengine_config
from ghidonations import tools


class RPCHandler(webapp2.RequestHandler):
    def __init__(self, request, response):
        super(RPCHandler, self).__init__()
        self.initialize(request, response)
        self.methods = RPCMethods()

    def get(self):
        self.response.headers['Access-Control-Allow-Origin'] = '*'
        authenticated = tools.RPCcheckAuthentication(self, True)
        # authenticated = True

        func = None
        action = self.request.get('action')

        if action:
            logging.info("Action: " + str(action))

            if action[0] == '_':
                self.error(403)  # access denied
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
                if authenticated is True:
                    func = getattr(self.methods, action, None)
                else:
                    self.error(401)
                    self.response.out.write("I'm not authorized to give you that information until you log in. Sorry!")

        if not func:
            self.error(404)  # method not found
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
            self.error(403)  # access denied
            return

        elif func[0:4] == "pub_":
            func = getattr(self.methods, func, None)

        elif func[0:5] == "semi_":
            if authenticated == "semi" or authenticated is True:
                func = getattr(self.methods, func, None)
            else:
                self.error(401)
                self.response.out.write("I'm not authorized to give you that information until you log in. Sorry!")

        else:
            if authenticated is True:
                func = getattr(self.methods, func, None)
            else:
                self.error(401)
                self.response.out.write("I'm not authorized to give you that information until you log in. Sorry!")

        if not func:
            self.error(404)  # file not found
            return

        result = func(*args)
        self.response.out.write(json.dumps(result))


# Set of functions that returns data to above GET request
class RPCMethods(object):
    # Every function here gives a success/fail and a response.
    # Even though there's no response needed, we have to return
    # something so it integrates with other functions
    # that do have a value to return. The response in that case is None

    # Globalhopeindia.org Utility Functions
    def pub_allTeams(self, settings):
        # This returns a json list of teams
        s = tools.getKey(settings).get()
        return [[t.name, t.key.urlsafe()] for t in s.data.display_teams]

    def pub_individualInfo(self, team_key, individual_key):
        i = tools.getKey(individual_key).get()
        t_key = tools.getKey(team_key)

        return i.data.info(t_key)

    def pub_teamInfo(self, team_key):
        # This returns a simplejson list of team members' names, hosted link to picture, and description
        # Response parsed by Javascript on main GHI site
        t = tools.getKey(team_key).get()
        return t.data.public_members_list


app = webapp2.WSGIApplication([
    ('/rpc', RPCHandler),
], debug=True)
app = appengine_config.recording_add_wsgi_middleware(app)
