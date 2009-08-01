import urllib2

from base import *
from pagination import PaginatedHandler

from models import Page, UserID, Feed

class MainHandler(PaginatedHandler):
	def all_instances(self):
		return Page.find_all(self.user())
	
	def get(self):
		user = self.user()
		
		bookmarklet_js = render('snippets/bookmarklet.js', {'host':host_for_url(self.uri())})
		bookmarklet_js.replace('\n', ' ')
		template_values = {
			'name': user.nickname(),
			'pages': self.paginated(self.all_instances()),
			'feed_link': Feed.path_for(user),
			'pagination': self.pagination_links(),
			'bookmarklet': urllib2.quote(bookmarklet_js)
		}
		debug("template values: %r" % template_values)
		
		self.response.out.write(render_page('index', template_values))

