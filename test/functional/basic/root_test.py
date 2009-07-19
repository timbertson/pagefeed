import urllib2
from google.appengine.api import users

from models import Page, UserID

from test_helpers import *

class RootTest(TestCase):
	
	def test_should_show_page_list_for_a_logged_in_user(self):
		page = fixtures.stub_page()
		response = fixtures.app().get('/')
		
		response.mustcontain('Welcome to PageFeed, foo')
		response.mustcontain(page.title)
	
	def test_should_link_to_feed_for_a_logged_in_user(self):
		page = fixtures.stub_page()
		response = fixtures.app().get('/')
		
		response.mustcontain(page.title)

		user = fixtures.a_user
		email = user.email()
		user_handle = UserID.get(email).handle
		
		feed_link = '/feed/%s-%s/' % (user_handle, urllib2.quote(email))
		content = response.body
		response.mustcontain('<link href="%s" type="application/rss+xml"' % (feed_link))
		response.mustcontain('<a href="%s"' % feed_link)
	
	def test_should_delete_items_and_redirect_to_root(self):
		page = fixtures.stub_page()
		response = fixtures.app().get('/')
		forms = response.forms
		delete_form = forms['delete_page_%s' % (page.key())]

		def check(owner, url):
			self.assertEqual(url, page.url)
			return page
			
		mock_on(Page).find.with_action(check)
		mock_on(page).delete.is_expected

		response = delete_form.submit().follow()
		self.assertEqual(response.request.url, 'http://localhost/')
		
	def test_should_update_items_and_redirect_to_root(self):
		page = fixtures.stub_page()
		response = fixtures.app().get('/')
		forms = response.forms
		update_form = forms['update_page_%s' % page.key()]
		
		def check(owner, url):
			self.assertEqual(url, page.url)
			return page
			
		mock_on(Page).find.with_action(check)
		mock_on(page).update.is_expected.with_(force=True)
		
		response = update_form.submit().follow()
		self.assertEqual(response.request.url, 'http://localhost/')
		
	

