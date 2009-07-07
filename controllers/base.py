from google.appengine.ext import webapp
from google.appengine.api import users

from server_errors import HttpError, RedirectError

import logging
from logging import debug, info, error
from helpers import view, render, render_page, host_for_url

class BaseHandler(webapp.RequestHandler):
	def handle_exception(self, exc, *a, **k):
		if isinstance(exc, HttpError):
			self.error(exc.code)
			self.response.out.write(exc.content)
			return
		if isinstance(exc, RedirectError):
			self.redirect(exc.target)
			return
		webapp.RequestHandler.handle_exception(self, exc, *a, **k)
		
	def user(self):
		user = users.get_current_user()
		if user:
			return user
		else:
			debug('no user - redirecting to "/"')
			raise RedirectError(users.create_login_url(self.request.uri))
		
	def url(self):
		url = self.request.get('url')
		if url:
			return url
		raise HttpError(400)
	
	def uri(self):
		return self.request.uri.split('?')[0]
	
