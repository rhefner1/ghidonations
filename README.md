GHI Donations
=============

GHI Donations organizes the donations of Global Hope India (http://globalhopeindia.org) and was engineered by Ryan Hefner (http://r.hefner1.com).

For much more information and in-depth documentation, check out [the project wiki](https://github.com/rhefner1/ghidonations/wiki).

The application does three major things:
 - Track donations (offline and from PayPal)
 - Manage teams that are fundraising
 - Organize contact information

It utilizes:

 - Google App Engine (Python 2.7)
 - App Engine NDB and webapp2 modules
 - JQuery frontend
 - Google Cloud Endpoints
 - Search API
 - And many others...

The four main modules are:
 - `DataModels.py` (contains all data models and methods)
 - `GlobalUtilities.py` (contains utility functions and many functions referenced by data models)
 - `endpoints.py` (contains the Cloud Endpoints API communication code)
 - `mooha.py` (the HTTP GET and POST web handlers)

## Installing
Before deploying, make `lib` and run `pip install -t lib -r requirements.txt`.