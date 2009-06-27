import wsgiref.handlers
from google.appengine.ext import webapp
from google.appengine.api import users
from google.appengine.ext.webapp import template

import os
from models import Page

class BaseHandler(webapp.RequestHandler):
	def user(self):
		user = users.get_current_user()
		if user:
			return user
		else:
			self.redirect(users.create_login_url(self.request.uri))
		
	def url(self):
		url = self.request.get_all('url')
		if url:
			return url
		return self.error(400)

class MainHandler(BaseHandler):
	def _add(self, user, url):
		existing = Page.find(user, url)
		if existing is None:
			Page(owner=self.user(), url=url).put()
			return True
		return False

	def get(self):
		url = self.request.get('url')
		if url:
			added = self._add(self.user(), url)
			self.response.out.write('%s URL: %s' % ('added' if added else 'ignored', url))
		else:
			user = self.user()
			template_values = {
				'user': user,
				'pages': Page.find_all(user),
				'uri': self.request.uri,
			}
			path = os.path.join(os.path.dirname(__file__), 'index.rss')
			self.response.out.write(template.render(path, template_values))

	def post(self):
		self._add(self.user(), self.url())

	def delete(self):
		Page.find(owner=self.user(), url=self.url()).delete()
		
def main():
	application = webapp.WSGIApplication([
		('/', MainHandler),
		], debug=True)
	wsgiref.handlers.CGIHandler().run(application)

if __name__ == '__main__':
	main()
