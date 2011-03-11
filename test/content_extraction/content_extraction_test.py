from test_helpers import *
from pagefeed.models import Page, Content
from pagefeed.models import page as page_module
from pagefeed.content_extraction import view_text, native
from google.appengine.api.urlfetch import fetch, DownloadError
from google.appengine.ext import deferred
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

class NativeContentExtractionParsing(CleanDBTest):
	def extract(self, content, url=some_url):
		p = Page(url=url, _raw_content=content, owner=a_user)
		return native.extract(p)

	def test_should_load_well_formed_page(self):
		content = """
			<html>
			<title>the title!</title>
			<body>the body!</body>
			</html>
			"""
		content = self.extract(content)
		self.assertEqual(content.title, 'the title!')
		self.assertEqual(content.body, '<body>the body!</body>')

	def assertContains(self, needle, haystack):
		self.assertTrue(needle in haystack, "could not find %s in %s" % (needle, haystack))

	def test_should_absoluteize_links_and_images(self):
		content = """
			<html>
			<title>the title!</title>
			<body>
				<a href="rel.html">rel</a>
				<a href="/path/to/pathed.html">pathed</a>
				<a href="http://google.com/abs.html">abs</a>
				<img src="/path/to/path2.jpg" />
			</body>
			</html>
			"""
		url =      'http://localhost/some/path/to_page.html'
		rel_base = "http://localhost/some/path/"
		base =     "http://localhost/"
		
		content = self.extract(content, url=url)
		self.assertContains('<a href="%srel.html">' % rel_base        , content.body)
		self.assertContains('<a href="%spath/to/pathed.html">' % base , content.body)
		self.assertContains('<a href="http://google.com/abs.html">'   , content.body)
		self.assertContains('<img src="%spath/to/path2.jpg" />' % base, content.body)

	def test_should_remove_a_bunch_of_unwanted_html_attributes(self):
		html = """
				<html>
					<p style="border-color:#ff; background:#fff;" COLOR="foo" alt="lala">
						<img src="http://localhost/blah" width  =  100 height=  20px />
						<div bgcolor=foo>
							so then style=none should not be stripped
							<span bgcolor-andthensome="not_strippped"></span>
						</div>
					</p>
				</html>
			"""
		expected_html = """
				<html>
					<p alt="lala">
						<img src="http://localhost/blah" />
						<div>
							so then style=none should not be stripped
							<span bgcolor-andthensome="not_strippped"></span>
						</div>
					</p>
				</html>
			"""
		content = self.extract(html)
		print "ACTUAL: " + content.body
		print '-----'
		print "EXPECTED: " + expected_html
		self.assertEqual(content.body.strip().replace('\t',''), expected_html.strip().replace('\t',''))

	def test_should_fall_back_to_entire_html_if_it_has_no_body(self):
		html = "<html><title>no body</title></html>"
		content = self.extract(html)
		self.assertEqual(content.title, 'no body')
		self.assertEqual(content.body, html)

	def test_should_strip_out_script_and_style_and_link_tags(self):
		html = "<html><body><script></script><style></style><link /></body>"
		content = self.extract(html)
		self.assertEqual(content.body, "<body></body>")
	
	def test_should_accept_multiline_titles(self):
		html = "<title>foo\nbar</title>"
		self.assertEqual(self.extract(html).title, "foo bar")

	def test_should_save_blank_contents_if_it_cannot_parse_html(self):
		html = '<title><scr " + ipt> + "foo\nbar</title><body>fjdklfsj</body>'
		def all_contents():
			return Content.all().fetch(5)
		self.assertEquals(len(all_contents()), 0)
		try:
			self.extract(html, url=some_url)
			self.fail()
		except deferred.PermanentTaskFailure:
			self.assertEquals(len(all_contents()), 1)
			content = all_contents()[0]
			self.assertEqual(content.title, None)
			self.assertEqual(content.body, None)

