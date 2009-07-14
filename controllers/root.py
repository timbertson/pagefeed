import urllib2

from base import *
from models import Page, UserID, Feed

class MainHandler(BaseHandler):
	def get(self):
		user = self.user()
		
		bookmarklet_js = render('snippets/bookmarklet.js', {'host':host_for_url(self.uri())})
		bookmarklet_js.replace('\n', ' ')
		template_values = {
			'name': user.nickname(),
			'pages': Page.find_all(user),
			'feed_link': Feed.path_for(user),
			'logout': users.create_logout_url('/'),
			'bookmarklet': urllib2.quote(bookmarklet_js)
		}
		debug("template values: %r" % template_values)
		
		self.response.out.write(render_page('index', template_values))

