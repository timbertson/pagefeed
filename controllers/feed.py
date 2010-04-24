import urllib2
from models import Page, UserID
from token_auth import auth

from base import *

class FeedHandler(BaseHandler):
	# note: doesn't require a logged-in user()
	# authentication is handled by the secret (but non-sensitive) user handle
	# in addition to email address
	def get(self, handle, email):
		user = auth(handle, email)
		template_values = {
			'user': user.nickname(),
			'pages': Page.find_all(user).fetch(limit=50),
			'uri': self.uri(),
		}
		debug("template values: %r" % (template_values,))
		self.response.out.write(render('feed.rss', template_values))

