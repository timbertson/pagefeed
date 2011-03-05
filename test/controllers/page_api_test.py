from test_helpers import *
from pagefeed.models import Page
from pagefeed.controllers import PageListHandler, PageHandler
from pagefeed.server_errors import HttpError
from StringIO import StringIO

class PageApiTest(TestCase):
	def handler(self, cls):
		handler = cls()
		when(handler).user().then_return(a_user)
		handler.response = Object('response')
		handler.response.out = StringIO()
		when(handler).is_json().then_return(True)
		return handler
	
	def response(self, handler):
		return handler.response.out.getvalue()

	def test_should_list_all_pages_for_a_user_in_JSON(self):
		handler = self.handler(PageListHandler)

		page1 = mock('page1').with_methods(json_attrs={'page':1})
		page2 = mock('page2').with_methods(json_attrs={'page':2})

		expect(Page).find_all(a_user).and_return([page1, page2])

		handler.get()
		self.assertEqual(self.response(handler), '[{"page": 1}, {"page": 2}]')

	def test_should_fetch_a_single_page(self):
		handler = self.handler(PageHandler)
		page = mock('page').with_children(content='content!')
		modify(handler).request = {'url': 'url'}
		expect(Page).find(owner=a_user, url="url").and_return(page)
		handler.get()
		self.assertEqual(self.response(handler), 'content!')

	def test_fetching_content_should_fail_for_a_page_without_content(self):
		handler = self.handler(PageHandler)
		page = mock('page').with_children(content=None)
		modify(handler).request = {'url': 'url'}
		expect(Page).find(owner=a_user, url="url").and_return(page)
		self.assertRaises(HttpError, handler.get, args=(404, 'could not find content for page: url'))

