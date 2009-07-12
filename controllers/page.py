import cgi

from base import *
from models import Page

class PageHandler(BaseHandler):
	def _add(self, user, url, success = None):
		page = Page.find(user, url)
		if page is None:
			page = Page(owner=self.user(), url=url)
			page.put()
		else:
			page.update()
		if page.errors:
			self._render_error(page)
		else:
			if success is not None:
				success(page)
		return page
	
	def _render_error(self, page):
		self.response.out.write(render_page('error', {'page':page, 'title':'error'},))

	def post(self):
		page = self._add(self.user(), self.url(), success = lambda x: self.redirect('/'))

	def delete(self):
		page = Page.find(owner=self.user(), url=self.url())
		if page:
			page.delete()
			self.response.out.write("deleted")
			self.redirect('/')
		else:
			info("could not find page: %s" % (self.url(),))
			raise HttpError(404, "could not find saved page: %s" % (cgi.escape(self.url(),)))

class PageBookmarkletHandler(PageHandler):
	def get(self):
		def success(page):
			self.response.out.write(render('bookmarklet.html', {}))
		self._add(self.user(), self.url(), success=success)
	

class PageDeleteHandler(PageHandler):
	# alias for DELETE on PageHandler
	get = post = PageHandler.delete
