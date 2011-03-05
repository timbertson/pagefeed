from test_helpers import *
from pagefeed.models import Page
from pagefeed.content_extraction import view_text, native
from google.appengine.api.urlfetch import fetch, DownloadError

class ContentExtractionTest(TestCase):

	def test_should_fetch_article_from_viewtext(self):
		page = mock('page').with_children(content_url='http://example.com/example')
		response = mock('response').with_children(status_code=200)
		response.content = '{"content":"<html><p>Hello there!</p></html>", "title":"Title of Content"}'
		when(view_text).fetch(\
				object_containing('url=http%3A//example.com/example'), allow_truncated=False, **any_kwargs).\
				then_return(response)
		view_text.extract(page)
	
	def test_should_fetch_article_directly(self):
		pass

	def test_should_treat_failed_fetches_as_None_content(self):
		pass

	def test_should_accept_the_best_content(self):
		pass

	def test_reload_should_mark_content_as_requiring_fetch_again(self):
		pass

