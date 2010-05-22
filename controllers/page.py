import cgi

from base import *
from models import Page

class PageHandler(BaseHandler):
	def _add(self, user, url, success = None, force=False):
		new_page = None
		page = Page.find(user, url)
		if page is None:
			page = Page(owner=self.user(), url=url)
			page.put()
			new_page = page
		else:
			page.update(force=force)
			if force:
				new_page = page
		if page.errors:
			self._render_error(page)
		else:
			if success is not None:
				success(new_page)
		return new_page
	
	def _render_error(self, page):
		if self.is_ajax():
			self.error(500)
		self.response.out.write(render_page('error', {'page':page, 'title':'error'}, partial=self.is_ajax()))

	def post(self):
		page = self._add(self.user(), self.url(), success = self._render_success)

	def delete(self):
		page = Page.find(owner=self.user(), url=self.url())
		if page:
			page.delete()
			if not self.is_ajax():
				self.redirect('/')
		else:
			info("could not find page: %s" % (self.url(),))
			raise HttpError(404, "could not find saved page: %s" % (cgi.escape(self.url(),)))
	
	def _render_success(self, page):
		if self.is_ajax():
			if page is not None:
				self.response.out.write(render("snippets/page_summary.html", {'page':page}))
		else:
			self.redirect('/')

class PageBookmarkletHandler(PageHandler):
	def get(self):
		def success(page):
			self.response.out.write(render('bookmarklet.html', {}))
		self._add(self.user(), self.url(), success=success)
	

class PageDeleteHandler(PageHandler):
	# alias for DELETE on PageHandler
	get = post = PageHandler.delete

class PageUpdateHandler(PageHandler):
	def post(self):
		page = self._add(self.user(), self.url(), success = self._render_success, force=True)

class PageListHandler(BaseHandler):
	def get(self):
		pages = Page.find_all(self.user())
		self.response.out.write("\n".join(page.url.encode('UTF-8') for page in pages))
