
from mocktest import *

from pagefeed.models.page import Page
from user import a_user
from app import app

def stub_page(page=None, url='http://localhost/whatever'):
	mock_on(Page).fetch
	if page is None:
		page = Page(url=url, title='page title', owner=a_user)
	page.put()

	all_pages = mock('all pages')
	all_pages.with_methods(count=1, fetch=[page])
	
	mock_on(Page).find_all.returning(all_pages.raw)
	return page


class PageDriver(object):
	app = None
	def __init__(self):
		if self.app is None:
			self.app = app()

	def add(self, url):
		return self.app.post('/page/', {'url':url})

	def delete(self, url, **kwargs):
		return self.app.post('/page/del/', {'url':url}, **kwargs)



