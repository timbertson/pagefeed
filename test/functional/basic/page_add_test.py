from pagefeed.test.helpers import *
from models import page
from google.appengine.api import users

from pagefeed.test import fixtures

class PageAddTest(TestCase):
	def test_should_add_a_page_and_redirect_to_root(self):
		url = 'http://localhost/page_to_save'
		mock_page = mock('response').with_children(status_code=200, content='')
		mock_on(page).fetch.returning(mock_page.raw).is_expected.with_(url)

		response = fixtures.app().post('/page/', {'url':url})
		self.assertFalse(page.Page.find(fixtures.a_user, url).error)
		response.follow().mustcontain('Welcome')
		self.assertEqual(response.follow().request.url, fixtures.app_root)

	def test_should_add_a_page_and_display_error_for_a_malformed_page(self):
		url = 'http://localhost/page_to_save'
		mock_page = mock('response').with_children(status_code=200, content='this is <not valid </html')
		mock_on(page).fetch.returning(mock_page.raw).is_expected.with_(url)

		response = fixtures.app().post('/page/', {'url':url})
		self.assertTrue(page.Page.find(fixtures.a_user, url).error)

		response.mustcontain('error')

	
	

