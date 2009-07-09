from pagefeed.test.helpers import *
from models.page import Page
from google.appengine.api import users

from pagefeed.test.functional import mocks

class RootTest(TestCase):
	
	def test_should_show_page_list_for_a_logged_in_user(self):
		page = mocks.stub_page()
		response = mocks.app().get('/')
		
		response.mustcontain('Welcome, foo')
		response.mustcontain(page.title)
	
	def test_should_delete_items_and_redirect_to_root(self):
		page = mocks.stub_page()
		response = mocks.app().get('/')
		forms = response.forms
		delete_form = forms[1]
		
		def check(owner, url):
			self.assertEqual(url, page.url)
			return page
			
		mock_on(Page).find.with_action(check)
		
		response = delete_form.submit().follow()
		self.assertEqual(response.request.url, 'http://localhost/')
		
	

