import urllib2

from base import *
from pagination import PaginatedHandler

from pagefeed.models import Page, UserID, Feed

class MainHandler(PaginatedHandler):
	def all_instances(self):
		return Page.find_all(self.user())
	
	def is_kindle(self):
		return 'kindle/' in str(self.request.headers.get('User-Agent', '')).lower()
	
	def get(self):
		user = self.user()
		
		host = host_for_url(self.uri())
		bookmarklet_js = render('snippets/bookmarklet.js', {'host':host})
		bookmarklet_js.replace('\n', ' ')
		feed_url = Feed.url_for(user, host)

		template_values = {
			'name': user.nickname(),
			'pages': self.paginated(self.all_instances()),
			'feed_link': feed_url,
			'pagination': self.pagination_links(),
			'bookmarklet': urllib2.quote(bookmarklet_js)
		}
		if self.is_kindle():
			template_values['custom_css'] = 'kindle'
		debug("template values: %r" % template_values)
		
		self.response.out.write(render_page('index', template_values))
