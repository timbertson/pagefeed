import cgi

from google.appengine.ext.webapp import template

from models import Page, UserID
from base import BaseHandler
from helpers import view
from errors import HttpError

import logging
from logging import debug, info

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
		self.response.out.write(template.render(view('error.html'), {'page':page}))

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
			self.response.out.write(template.render(view('bookmarklet.html'), {}))
		self._add(self.user(), self.url(), success=success)
	

class PageDeleteHandler(PageHandler):
	# alias for DELETE on PageHandler
	get = post = PageHandler.delete
