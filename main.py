#!/usr/bin/env python

import wsgiref.handlers
from google.appengine.ext import webapp
from google.appengine.api import users
from google.appengine.ext.webapp import template

import os
import urllib
import cgi
import urllib2
from models import Page, UserID

def path(*parts):
	return os.path.join(os.path.dirname(__file__), *parts)

class HttpError(Exception):
	def __init__(self, code, content=''):
		self.code = code
		self.content = ''

class RedirectError(Exception):
	def __init__(self, target):
		self.target = target

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
			raise RedirectError(users.create_login_url(self.request.uri))
		
	def url(self):
		url = self.request.get('url')
		if url:
			return url
		raise HttpError(400)
	
	def uri(self):
		return self.request.uri.split('?')[0]
	

class MainHandler(BaseHandler):
	def get(self):
		user = self.user()
		email = user.email()
		user_handle = UserID.get(email).handle
		uri = self.uri() + 'feed/%s-%s/' % (user_handle, urllib.quote(email))
		
		bookmarklet_js = template.render(path('bookmarklet.js'), {'host':self.uri().split('/')[2]})
		bookmarklet_js.replace('\n', ' ')
		template_values = {
			'name': user.nickname(),
			'pages': Page.find_all(user),
			'feed_link': uri,
			'logout': users.create_logout_url('/'),
			'bookmarklet': urllib2.quote(bookmarklet_js)
		}
		
		self.response.out.write(template.render(path('index.html'), template_values))

class FeedHandler(BaseHandler):
	# note: doesn't require a logged-in user()
	# authentication is handled by the secret (but non-sensitive) user handle
	# in addition to email address
	def get(self, handle, email):
		email = urllib.unquote(email)
		if not UserID.auth(email, int(handle)):
			raise HttpError(403, "invalid credentials... ")
		user = users.User(email)
		template_values = {
			'user': user.nickname(),
			'pages': Page.find_all(user),
			'uri': self.uri(),
		}
		self.response.out.write(template.render(path('feed.rss'), template_values))

class PageHandler(BaseHandler):
	def _add(self, user, url, success = None):
		page = Page.find(user, url)
		if page is None:
			page = Page(owner=self.user(), url=url)
			page.put()
		else:
			page.update()
		if page.error:
			self._render_error(page)
		else:
			if success is not None:
				success(page)
		return page
	
	def _render_error(self, page):
		self.response.out.write(template.render(path('error.html'), {'page':page}))

	def post(self):
		page = self._add(self.user(), self.url(), success = lambda x: self.redirect('/'))

	def delete(self):
		page = Page.find(owner=self.user(), url=self.url())
		if page:
			page.delete()
			self.response.out.write("deleted")
			self.redirect('/')
		else:
			raise HttpError(404, "could not find saved page: %s" % (cgi.escape(self.url(),)))

class PageBookmarkletHandler(PageHandler):
	def get(self):
		def success(page):
			self.response.out.write(template.render(path('bookmarklet.html'), {}))
		self._add(self.user(), self.url(), success=success)
	

class PageDeleteHandler(PageHandler):
	# alias for DELETE on PageHandler
	get = post = PageHandler.delete

def main():
	application = webapp.WSGIApplication([
		('/', MainHandler),
		('/page/', PageHandler),
		('/page/bookmarklet/', PageBookmarkletHandler),
		('/page/del/', PageDeleteHandler),
		(r'/feed/(\d+)-([^/]+)/', FeedHandler),
		], debug=True)
	wsgiref.handlers.CGIHandler().run(application)

if __name__ == '__main__':
	main()
