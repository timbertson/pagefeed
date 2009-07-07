from pagefeed.test.helpers import *
from models.page import Page
from google.appengine.api import users

from webtest import TestApp

class RootTest(TestCase):
	user = 'foo@example.com'
	def app(self):
		import os
		from pagefeed.main import application
		os.environ['USER_EMAIL'] = self.user
		os.environ['SERVER_NAME'] = 'localhost'
		os.environ['SERVER_PORT'] = '8000'
		return TestApp(application)

	def test_should_show_page_list_for_a_logged_in_user(self):

		mock_on(Page).fetch
		page = Page(url='http://localhost/whatever', title='page title', owner=users.User('foo'))
		page.put()
		page_id = page.key()

		mock_on(Page).find_all.returning([page])
		response = self.app().get('/')
		
		response.mustcontain('Welcome, foo')
		response.mustcontain('page title')
		
		forms = response.forms
		print repr(forms[1])
		response.mustcontain(page_id)
		
	

