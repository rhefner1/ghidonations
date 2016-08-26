import logging
import urllib

from ghidonations.http_handlers.base import BaseHandlerAdmin
from ghidonations.tools import auth
from google.appengine.ext import blobstore
from google.appengine.ext.webapp import template, blobstore_handlers


class ExportDonations(BaseHandlerAdmin):
    def task(self, is_admin, s):
        template_variables = {}
        self.response.write(
            template.render('pages/export_donations.html', template_variables))


class SpreadsheetDownload(blobstore_handlers.BlobstoreDownloadHandler):
    def get(self):
        auth.check_authentication(self, True)

        str_blob_key = urllib.unquote(self.request.get("blob_key"))
        blob_key = blobstore.BlobInfo.get(str_blob_key)

        if not blobstore.get(str_blob_key):
            logging.error("404 on blob key: " + str_blob_key)
            self.error(404)
        else:
            logging.info("Serving blob: " + str_blob_key)
            self.send_blob(blob_key, save_as=True)