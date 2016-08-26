import webapp2

import appengine_config
from ghidonations.http_handlers.auth import Login, Logout, NotAuthorized
from ghidonations.http_handlers.base import Container
from ghidonations.http_handlers.dashboard import Dashboard
from ghidonations.http_handlers.data_list import AllContacts, AllDeposits, AllIndividuals, AllTeams, TeamMembers, \
    UndepositedDonations
from ghidonations.http_handlers.data_single import Contact, Deposit, Settings
from ghidonations.http_handlers.donor_report import DonorReport, DonorReportSelect
from ghidonations.http_handlers.export import ExportDonations, SpreadsheetDownload
from ghidonations.http_handlers.ipn import IPN
from ghidonations.http_handlers.letters import ThankYou
from ghidonations.http_handlers.merge_contacts import MergeContacts
from ghidonations.http_handlers.mobile import Mobile, MobileRedirectSetting
from ghidonations.http_handlers.new_data import NewContact, NewIndividual, NewTeam, OfflineDonation
from ghidonations.http_handlers.profile import IndividualProfile, UpdateProfile
from ghidonations.http_handlers.public_donate import DonatePage
from ghidonations.http_handlers.review_queue import ReviewQueue, ReviewQueueDetails

app = webapp2.WSGIApplication([
    ('/ajax/allcontacts', AllContacts),
    ('/ajax/alldeposits', AllDeposits),
    ('/ajax/allindividuals', AllIndividuals),
    ('/ajax/allteams', AllTeams),
    ('/ajax/contact', Contact),
    ('/', Container),
    ('/ajax/dashboard', Dashboard),
    ('/ajax/deposit', Deposit),
    ('/donate', DonatePage),
    ('/reports/donor', DonorReport),
    ('/ajax/donorreport', DonorReportSelect),
    ('/ajax/exportdonations', ExportDonations),
    ('/ajax/profile', IndividualProfile),
    ('/login', Login),
    ('/logout', Logout),
    ('/ajax/mergecontacts', MergeContacts),
    ('/m', Mobile),
    ('/ajax/newcontact', NewContact),
    ('/ajax/newindividual', NewIndividual),
    ('/ajax/newteam', NewTeam),
    ('/m/redirect', MobileRedirectSetting),
    ('/ajax/notauthorized', NotAuthorized),
    ('/ajax/offline', OfflineDonation),
    ('/ajax/review', ReviewQueue),
    ('/ajax/reviewdetails', ReviewQueueDetails),
    ('/ajax/settings', Settings),
    ('/ajax/spreadsheet/download', SpreadsheetDownload),
    ('/ajax/teammembers', TeamMembers),
    ('/thanks', ThankYou),
    ('/ajax/undeposited', UndepositedDonations),
    ('/ajax/profile/upload', UpdateProfile),
    ('/ipn', IPN)],
    debug=True)

app = appengine_config.webapp_add_wsgi_middleware(app)
app = appengine_config.recording_add_wsgi_middleware(app)
