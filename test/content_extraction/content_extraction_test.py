from test_helpers import *
from pagefeed.models import Page, Content
from pagefeed.models import page as page_module
from pagefeed.content_extraction import view_text, native
from google.appengine.api.urlfetch import fetch, DownloadError
from datetime import datetime, timedelta

def put(*objs):
	map(lambda o: o.put(), objs)

class ContentExtractionTest(CleanDBTest):
	def test_should_accept_the_best_content(self):
		page = Page(url=some_url, owner=a_user, pending=True)
		content1 = Content(url=some_url, title='bad', body='not much')
		content2 = Content(url=some_url, title='good', body='much more voluminous content')
		put(page, content1, content2)
		expect(Content).for_url(some_url).and_return([content1, content2])
		page_module.task_store_best_content(page.key())
		page = Page.get(page.key())
		self.assertEqual(page.title, content2.title)
		self.assertEqual(page.content, content2.body)

	def test_content_should_be_purged_if_it_is_older_than_1_day(self):
		old_content = Content(url=some_url, body='old body', title='old title', lastmod = datetime.utcnow() - timedelta(days=1, minutes=1))
		new_content = Content(url=some_url, body='new body', title='new title')
		old_content.put()
		new_content.put()
		Content.purge()
		kept_content = list(Content.all())
		self.assertEqual(kept_content, [new_content])

class ViewTextContentExtraction(TestCase):
	def test_should_fetch_article_from_viewtext(self):
		page = mock('page').with_children(content_url='http://example.com/example')
		response = mock('response').with_children(status_code=200)
		response.content = '{"content":"<html><p>Hello there!</p></html>", "title":"Title of Content"}'
		when(view_text).fetch(\
				object_containing('url=http%3A//example.com/example'), allow_truncated=False, **any_kwargs).\
				then_return(response)
		content = view_text.extract(page)
		self.assertEqual(content.title, 'Title of Content')
		self.assertEqual("".join(content.body.split('\n')), '<html><p>Hello there!</p></html>')
	
class NativeContentExtraction(TestCase):
	def test_should_fetch_article_using_native_extractor(self):
		page = mock('page').with_children(content_url='http://example.com/example', raw_content="""
			<html>
			<title>Title of Content</title>
			<body>
			<script src="malicious.js"/>
			<p>Hello there!</p>
			</body>
			</html>
		""")
		content = native.extract(page)
		self.assertEqual(content.title, 'Title of Content')
		self.assertEqual("".join(content.body.split('\n')), '<body><p>Hello there!</p></body>')

