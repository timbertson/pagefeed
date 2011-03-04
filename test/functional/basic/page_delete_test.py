from test_helpers import *
from pagefeed.models.page import Page

class PageDeleteTest(TestCase):
	def delete(self, url, **kwargs):
		return PageDriver().delete(url, **kwargs)

	def test_should_delete_a_page_and_redirect_to_root(self):
		url = 'http://localhost/page_to_delete'
		page = fixtures.stub_page(url=url)
		expect(Page).find(owner=fixtures.a_user, url=url).and_return(page)

		expect(page).delete()

		response = self.delete(url)
		print "content: %s" % (response.body,)
		self.assertEqual(response.follow().request.url, fixtures.app_root)

	def test_should_not_return_404_if_there_is_no_such_url(self):
		url = 'http://localhost/this_page_does_not_exist'
		expect(Page).find(owner=fixtures.a_user, url=url).and_return(None)
		self.delete(url, status=404)


