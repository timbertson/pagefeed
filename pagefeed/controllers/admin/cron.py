import logging
from pagefeed import pagefeed_path
from google.appengine.ext import webapp
from google.appengine.api import users

from pagefeed.models import Content

class ContentCronHandler(webapp.RequestHandler):
	def get(self):
		assert users.is_current_user_admin()
		logging.info("purging old content entries")
		Content.purge()
		logging.info("finished purging old content entries")
		self.response.out.write("ok")

