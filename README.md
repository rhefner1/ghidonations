GHI Donations
=============

GHI Donations organizes the donations of Global Hope India (http://globalhopeindia.org) and was engineered by Ryan Hefner (http://r.hefner1.com).

The application does three major things:
 - Track donations (offline and from PayPal)
 - Manage teams that are fundraising
 - Organize contact information

It utilizes:

 - Google App Engine (Python 2.7)
 - App Engine NDB and webapp2 modules
 - JQuery frontend
 - And much more...

The four main modules are:
 - DataModels.py (contains all data models and methods)
 - GlobalUtilities.py (contains utility functions and many functions referenced by data models)
 - rpc.py (contains the RPC client-server communication code)
 - mooha.py (the HTTP GET and POST web handlers)

 For more information and in-depth documentation, check out [the project wiki](https://github.com/rhefner1/ghidonations/wiki/GHI-Donations).