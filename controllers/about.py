from base import *
class AboutHandler(BaseHandler):
	def get(self):
		self.response.out.write(render_page('about', {}))


