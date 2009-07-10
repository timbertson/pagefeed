from pagefeed.test.helpers import *
from models import page as pagemodule
from google.appengine.api import users

from pagefeed.test import fixtures

class PageDeleteTest(TestCase):
	def delete(self, url, **kwargs):
		return fixtures.app().post('/page/del/', {'url':url}, **kwargs)

	def test_should_deleete_a_page_and_redirect_to_root(self):
		url = 'http://localhost/page_to_delete'
		page = fixtures.stub_page(url=url)
		mock_on(pagemodule).find.is_expected.with_(fixtures.a_user, url).returning(page)

		mock_on(page).delete.is_expected

		response = self.delete(url)
		self.assertEqual(response.follow().request.url, fixtures.app_root)

	def test_should_not_return_404_if_there_is_no_such_url(self):
		url = 'http://localhost/this_page_does_not_exist'
		mock_on(pagemodule).find.is_expected.with_(fixtures.a_user, url).returning(None)
		response = self.delete(url, status=404)


