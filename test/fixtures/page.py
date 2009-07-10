
from mocktest import *

from models.page import Page
from user import a_user

def stub_page(page=None):
	mock_on(Page).fetch
	if page is None:
		page = Page(url='http://localhost/whatever', title='page title', owner=a_user)
	page.put()
	page_id = page.key()
	mock_on(Page).find_all.returning([page])
	return page


