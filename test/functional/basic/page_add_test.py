from test_helpers import *
from models import page

class PageAddTest(TestCase):
	def add(self, url):
		return PageDriver().add(url)

	def test_should_add_a_page_and_redirect_to_root(self):
		url = 'http://localhost/page_to_save'
		mock_page = mock('response').with_children(status_code=200, content='')
		when(page).fetch(url).then_return(mock_page.raw)

		response = self.add(url)
		self.assertFalse(page.Page.find(fixtures.a_user, url).errors)
		print response.body
		response.follow().mustcontain('Welcome')
		self.assertEqual(response.follow().request.url, fixtures.app_root)

	def test_should_add_a_page_and_display_error_for_a_malformed_page(self):
		url = 'http://localhost/page_to_save'
		mock_page = mock('response').with_children(status_code=200, content='this is <not valid </html')
		when(page).fetch(url).then_return(mock_page.raw)

		response = self.add(url)
		self.assertEqual(len(page.Page.find(fixtures.a_user, url).errors), 1)

		response.mustcontain('error')

