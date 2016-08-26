import logging
import quopri

import ghidonations.tools.keys
from ghidonations.http_handlers.base import BaseHandler
from ghidonations.tools import auth, util
from google.appengine.ext import blobstore
from google.appengine.ext.webapp import template, blobstore_handlers


class IndividualProfile(BaseHandler):
    def task(self, is_admin, s):

        if is_admin is True:
            # If an admin, they can get whatever user they want
            i_key = self.request.get("i")

            # if no key specified, go to admin's personal account
            if i_key == "":
                i_key = ghidonations.tools.keys.get_user_key(self)
            else:
                i_key = ghidonations.tools.keys.get_key(i_key)

        else:
            # If a regular user, they can ONLY get their own profile
            i_key = ghidonations.tools.keys.get_user_key(self)

        i = i_key.get()
        logging.info("Getting profile page for: " + i.name)

        # Creating a blobstore upload url
        upload_url = blobstore.create_upload_url('/ajax/profile/upload')

        template_variables = {"s": s, "i": i, "upload_url": upload_url, "is_admin": is_admin}
        self.response.write(
            template.render("pages/profile.html", template_variables))


class UpdateProfile(blobstore_handlers.BlobstoreUploadHandler):
    def post(self):
        # Has a new image been selected?
        change_image = True
        try:
            upload_files = self.get_uploads('new_photo')
            blob_info = upload_files[0]
        except Exception:
            change_image = False
            blob_info = None

        individual_key = self.request.get("individual_key")
        name = self.request.get("name")
        email = self.request.get("email")
        team = self.request.get("team_list").replace("=\r\n", "")
        description = quopri.decodestring(self.request.get("description"))
        password = self.request.get("password")
        show_donation_page = self.request.get("show_donation_page")
        show_progress_bar = self.request.get("show_progress_bar")

        if show_donation_page == "on":
            show_donation_page = True
        elif show_donation_page == "":
            show_donation_page = False

        if show_progress_bar == "on":
            show_progress_bar = True
        elif show_progress_bar == "":
            show_progress_bar = False

        i = ghidonations.tools.keys.get_key(individual_key).get()

        if change_image is True:
            new_blobkey = str(blob_info.key())
        else:
            new_blobkey = None

        logging.info("Saving profile for: " + name)

        i.update(name, email, team, description, new_blobkey, password, show_donation_page, show_progress_bar)

        self.redirect("/#profile?i=" + individual_key)