from pagefeed.test.helpers import *
from models.page import Page
from google.appengine.api import users

from webtest import TestApp

import os
from pagefeed.main import application
from lib.BeautifulSoup import BeautifulSoup

ROOT_URL = "http://localhost/"

class RootTest(TestCase):
	user = 'foo@example.com'
	def app(self):
		os.environ['USER_EMAIL'] = self.user
		os.environ['SERVER_NAME'] = 'localhost'
		os.environ['SERVER_PORT'] = '8000'
		return TestApp(application)

	def stub_page(self):
		mock_on(Page).fetch
		page = Page(url='http://localhost/whatever', title='page title', owner=users.User('foo'))
		page.put()
		page_id = page.key()
		mock_on(Page).find_all.returning([page])
		return page
	
	# ---
	
	def test_should_show_page_list_for_a_logged_in_user(self):
		page = self.stub_page()
		response = self.app().get('/')
		
		response.mustcontain('Welcome, foo')
		response.mustcontain(page.title)
	
	def test_should_delete_items_and_redirect_to_root(self):
		page = self.stub_page()
		response = self.app().get('/')
		forms = response.forms
		self.assertEqual(len(forms), 2) # 1 delete page, 1 add page
		delete_form = forms[1]
		
		def check(owner, url):
			self.assertEqual(url, page.url)
			return page
			
		mock_on(Page).find.with_action(check)
		
		response = delete_form.submit().follow()
		self.assertEqual(response.request.url, ROOT_URL)
	
	@pending
	def test_should_indicate_failed_items_and_allow_them_to_be_retried(self):
		page = self.stub_page()
		Page.fetch.is_expected.twice() # once for the initial save, and once for the update
		response = self.app().get('/')
		
		soup = BeautifulSoup(response.body)
		self.assertEqual(len(soup.findAll('dt', attrs={'class':'page error'})), 1)
		
		forms = response.forms
		update_form = forms[2]
		response = update_form.submit().follow()
		self.assertEqual(response.request.url, ROOT_URL)

		soup = BeautifulSoup(response.body)
		self.assertEqual(len(soup.findAll('dt', attrs={'class':'page error'})), 0)

