from base import *
class StaticHandler(BaseHandler):
	page_name = None
	def template_values(self):
		return {'title': self.page_name}

	def get(self):
		self.response.out.write(render_page(self.page_name.lower(), self.template_values()))

class AboutHandler(StaticHandler):
	page_name = 'About'

class FaqHandler(StaticHandler):
	page_name = 'FAQ'

