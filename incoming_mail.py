import logging, datetime, xmlrpclib, wsgiref.handlers

#App engine platform
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.ext import db
from google.appengine.ext.webapp.mail_handlers import InboundMailHandler
from google.appengine.api import urlfetch, mail
import webapp2 as webapp

#Application files
import GlobalUtilities as utilities


class GAEXMLRPCTransport(object):
    """Handles an HTTP transaction to an XML-RPC server."""

    def __init__(self):
        pass

    def request(self, host, handler, request_body, verbose=0):
        result = None
        url = 'http://%s%s' % (host, handler)
        try:
            response = urlfetch.fetch(url,
                                      payload=request_body,
                                      method=urlfetch.POST,
                                      headers={'Content-Type': 'text/xml'})
        except:
            msg = 'Failed to fetch %s' % url
            logging.error(msg)
            raise xmlrpclib.ProtocolError(host + handler, 500, msg, {})

        if response.status_code != 200:
            logging.error('%s returned status code %s' %
                          (url, response.status_code))
            raise xmlrpclib.ProtocolError(host + handler,
                                          response.status_code,
                                          "",
                                          response.headers)
        else:
            result = self.__parse_response(response.content)

        return result

    def __parse_response(self, response_body):
        p, u = xmlrpclib.getparser(use_datetime=False)
        p.feed(response_body)
        return u.close()

class LogSenderHandler(InboundMailHandler):
    def receive(self, mail_message):
        logging.info("Received a mail_message from: " + mail_message.sender)

        to = mail_message.to
        at_sign = to.find("@")
        settings_key = to[0:at_sign]

        s = utilities.getByKey(self, settings_key)

        if s.wp_url != None and s.wp_username != None and s.wp_password != None:
        
            title = mail_message.subject
            logging.info("Title: " + title)
            
            bodies = mail_message.bodies('text/html')
            if not bodies:
                bodies = mail_message.bodies('text/plain')
            
            #Decoding plaintext body
            for content_type, body in bodies:
                content = body.decode()
            
            logging.info("Content: " + content)

            wp_url = s.wp_url + "/xmlrpc.php"
            wp_username = s.wp_username
            wp_password = s.wp_password
            wp_blogid = ""

            status_draft = 0
            status_published = 1

            server = xmlrpclib.ServerProxy(wp_url, GAEXMLRPCTransport())

            today = datetime.datetime.today()
            date_created = xmlrpclib.DateTime(today)

            categories = []
            tags = []
            data = {'title': title, 'description': content, 'dateCreated': date_created, 'categories': categories, 'mt_keywords': tags}

            post_id = server.metaWeblog.newPost(wp_blogid, wp_username, wp_password, data, status_published)
            logging.info("Posted to Wordpress. Post ID: " + str(post_id))
            
        else:
            raise
        
            

app = webapp.WSGIApplication([
       LogSenderHandler.mapping()],
       debug=True)