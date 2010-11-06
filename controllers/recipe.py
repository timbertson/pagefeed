from base import *
from models import Feed

class RecipeHandler(BaseHandler):
	def get(self):
		host = host_for_url(self.uri())
		feed_url = Feed.url_for(self.user(), host)
		server_base = "http://%s" % (host,)

		self.response.headers['Content-Type'] ='application/python'
		self.response.headers['Content-Disposition'] = 'attachment; filename="pagefeed.recipe"'
		self.response.out.write(render('calibre.py', {'feed_url':feed_url, 'server_base':server_base}))
