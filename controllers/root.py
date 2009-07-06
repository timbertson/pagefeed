import urllib2

from base import *
from models import Page, UserID

class MainHandler(BaseHandler):
	def get(self):
		user = self.user()
		email = user.email()
		user_handle = UserID.get(email).handle
		uri = self.uri() + 'feed/%s-%s/' % (user_handle, urllib2.quote(email))
		
		bookmarklet_js = render('bookmarklet.js', {'host':host(self.uri())})
		bookmarklet_js.replace('\n', ' ')
		template_values = {
			'name': user.nickname(),
			'pages': Page.find_all(user),
			'feed_link': uri,
			'logout': users.create_logout_url('/'),
			'bookmarklet': urllib2.quote(bookmarklet_js)
		}
		debug("template values: %r" % template_values)
		
		self.response.out.write(render_page('index', template_values))
