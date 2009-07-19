from base import *

class LogoutHandler(BaseHandler):
	def post(self):
		self.redirect(users.create_logout_url('/about/'))

