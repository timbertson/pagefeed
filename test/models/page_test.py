from test_helpers import *
from pagefeed.models import page, Page, Transform, Content
from pagefeed.lib.BeautifulSoup import BeautifulSoup, UnicodeDammit
from pagefeed.content_extraction import native
from google.appengine.ext import deferred

some_url = 'http://localhost/dontcare'

class PageLifecycleTest(CleanDBTest):
	def setUp(self):
		super(PageLifecycleTest, self).setUp()
		self.defer_mock = mock(deferred).defer
		when(deferred).defer(*any_args, **any_kwargs).then_return(None)

	def test_page_should_start_with_no_content(self):
		p = Page(url=some_url, owner=a_user)
		self.assertEquals(p.content, None)
	
	def test_page_should_launch_tasks_to_populate_data(self):
		p = Page(url=some_url, owner=a_user)
		p.put()
		expect(page.Transform).process(p)
		expect(deferred).defer(page.task_extract_content, 'native', p.key())
		expect(deferred).defer(page.task_extract_content, 'view_text', p.key())
		p.start_content_population()

	def test_should_log_error_and_ignore_transforms_if_they_fail(self):
		modify(page).content_extractors = []

		p = Page(url=some_url, owner=a_user)

		expect(page.Transform).process(p).and_raise(page.TransformError("transform failed"))
		expect(p).error("transform failed")
		expect(deferred).defer(page.task_extract_content, *any_args).twice()

		p.start_content_population()
	
	def test_reset_should_clear_all_content(self):
		p = Page(url=some_url, owner=a_user)
		p.content = "content!"
		p._raw_content = "raw content!"
		p.title = "title"
		
		p.update(force=True)
		self.assertEquals(p.content, None)
		self.assertEquals(p.raw_content, None)
		self.assertEqual(p.title, "title")

	def test_store_best_content_should_do_nothing_if_not_all_processors_have_completed(self):
		p = Page(url=some_url, owner=a_user)
		p.put()
		modify(page).content_extractors = [1,2, 3, 4, 5, 6]
		when(Content).for_url(p.url).then_return([Content(url=some_url)])

		page.task_store_best_content(p.key())
		p = Page.get(p.key())
		self.assertEquals(p._title, None)
		self.assertEquals(p.content, None)

	def test_store_best_content_should_store_empty_values_if_forced(self):
		p = Page(url=some_url, owner=a_user)
		p.put()
		modify(page).content_extractors = [1,2, 3, 4, 5, 6]
		when(Content).for_url(p.url).then_return([])

		page.task_store_best_content(p.key(), force=True)
		p = Page.get(p.key())
		self.assertEquals(p.title, '[localhost saved item]')
		self.assertEquals(p.content, None)

	def test_store_best_content_should_do_so_if_all_extractors_are_complete(self):
		p = Page(url=some_url, owner=a_user, pending=True)
		p.put()
		modify(page).content_extractors = [1,2]

		best_content = Content(url=some_url, title='best title', body='best body')
		worst_content = Content(url=some_url)

		contents = [best_content, worst_content]

		when(Content).for_url(p.url).then_return(contents)

		page.task_store_best_content(p.key())

		p = Page.get(p.key())
		self.assertEquals(p.title, "best title")
		self.assertEquals(p.content, "best body")
	
	def test_store_best_content_should_do_nothing_if_content_is_already_set(self):
		p = Page(url=some_url, owner=a_user, pending=False)
		p.put()

		expect(Content).for_url.never()

		page.task_store_best_content(p.key())


class PageTest(CleanDBTest):
	def test_find_complete_should_skip_incomplete_pages(self):
		incomplete = Page(url=some_url, owner=a_user)
		complete = Page(url=some_url, owner=a_user, content='')
		[x.put() for x in (incomplete, complete)]
		pages = list(Page.find_complete(a_user))
		self.assertEquals(len(pages), 1)
		self.assertEqual(pages[0].key(), complete.key())
	

	def test_should_default_to_v1_page(self):
		self.assertEqual(1, Page(url=some_url, owner=a_user).version)

	def test_should_convert_v0_page_to_v1_page(self):
		# for reference, the v0 properties are:
		#class Version1Page(db.Model):
		#	version = db.IntegerProperty()
		#	url = db.URLProperty(required=True)
		#	_content_url = db.URLProperty()
		#	content = db.TextProperty()
		#	title = db.StringProperty()
		#	owner = db.UserProperty(required=True)
		#	date = db.DateTimeProperty(auto_now_add=True)
		#	_messages = db.StringListProperty()

		expect(page.deferred).defer.never()

		p = Page(version=0, url=some_url, _content_url=some_url + "/content", content='content', title='title',
				owner=a_user, _messages = ['info something bad happened...'])
		p.put()
		p = Page.get(p.key())
		self.assertEqual(p.version, 1)
		self.assertEqual(p.url, some_url)
		self.assertEqual(p.content, 'content')
		self.assertEqual(p.title, "title")
		self.assertEqual(p.owner, a_user)
		self.assertEqual(p._messages, ['info something bad happened...'])
		self.assertEqual(p.content_url, some_url + "/content")
	
	def test_should_omit_page_fragment_from_request(self):
		result = mock('result')
		modify(result).children(status_code=200, content='blah')
		url = 'http://localhost/some/path'
		full_url = url + "#anchor"
		expect(page).fetch(url, **any_kwargs).and_return(result)
		
		p = new_page(url=full_url)
		self.assertEqual(p.url, full_url)
		self.assertEqual(p.raw_content, 'blah')
		self.assertFalse(p.errors)

	def test_should_fall_back_to_a_default_title_containing_host(self):
		stub_result("<html><body>no title...</body></html>")
		p = new_page(url="http://google.com/blah")
		self.assertEqual(p.title, '[google.com saved item]')
		self.assertFalse(p.errors)
	
	@pending("cant insert failure condition properly...")
	def test_should_fall_back_to_a_default_title_if_no_host_available(self):
		stub_result("<html><body>no title...</body></html>")
		p = page.Page(url='http://localhost', owner=a_user)
		mock_on(p)._get_host.raising(StandardError)
		p.put()
		
		self.assertEqual(p.title, '[pagefeed saved item]')
		self.assertTrue("no title..." in p.content)
		self.assertFalse(p.errors)

	def test_should_apply_all_matching_transforms(self):
		filter1 = mock('filter1')
		filter2 = mock('filter2')
		filters = [filter1, filter2]

		p = page.Page(owner=a_user, url='http://sub.localhost.com/some/path/to/file.html')
		content = 'initial content'
		response = mock('response').with_children(status_code=200, content=content)
		when(page).fetch.then_return(response)
		soup = BeautifulSoup(content)
		soup2 = mock('second soup')

		expect(Transform).find_all(user=a_user, host='sub.localhost.com').and_return(filters)
		expect(filter1).apply(p, soup).and_return(soup2)
		expect(filter2).apply(p, soup2)
		p.put()
		p.apply_transforms()

	def test_should_fetch_content_from_new_url(self):
		old_url = 'http://old_url'
		new_url = 'http://new_url'
		p = new_page(content='initial content', url=old_url)

		response = mock('response').with_children(status_code=200, content='new content')
		expect(page).fetch(new_url, **any_kwargs).and_return(response)
		p.use_content_url(new_url)

		self.assertEqual(p.url, old_url)
		self.assertEqual(p.content_url, new_url)
		self.assertEqual(p.raw_content, 'new content')
	
	def test_should_detect_encoding_and_store_unicode_content(self):
		p = new_page(url=some_url)

		content_unicode = u'caf\xe9'
		response = mock('response').with_children(status_code=200,
			content=content_unicode.encode('UTF-8'),
			headers={'Content-Type':'text/html'})
		expect(page).fetch(some_url, **any_kwargs).and_return(response)

		self.assertEqual(p.raw_content, content_unicode)
		self.assertTrue(isinstance(p.raw_content, unicode))
	
	def test_should_use_encoding_from_http_headers(self):
		# known content that beautifulsoup will detect as windows-1521
		content = '\t\t\t"Kuzey r\xfczgari" (2007) {(#1.2)}  [Kaz\xc4\xb1m]\n'
		expected_unicode = content.decode('ISO-8859-2')

		p = new_page(url=some_url)

		response = mock('response').with_children(status_code=200,
			content=content,
			headers={'Content-Type':'text/html; ISO-8859-2'})
		expect(page).fetch(some_url, **any_kwargs).and_return(response)

		self.assertEqual(p.raw_content, expected_unicode)
		self.assertNotEqual(UnicodeDammit(content).unicode, expected_unicode)
		self.assertTrue(isinstance(p.raw_content, unicode))

	@ignore("can't implement this with beautifulsoup yet...")
	def test_transforms_should_extract_xpath_elements(self):
		pass
	
	def test_should_note_an_error_when_download_fails(self):
		stub_result('', status_code = 400)
		p = new_page()
		self.assertEqual(p.raw_content, None)
		self.assertTrue(p.errors)

	def test_should_retry_a_failed_download_on_update(self):
		p = new_page()
		p.error("failure")
		expect(p)._reset()
		expect(p).start_content_population()
		p.update()

	def test_should_not_retry_a_successful_download_on_update(self):
		p = new_page()
		expect(p)._reset.never()
		p.update()

	def test_update_should_delete_existing_content(self):
		p = new_page()
		expect(Content).trash(p.content_url)
		p.update(force=True)

	def test_should_retry_a_successful_download_on_update_if_forced(self):
		stub_result('')
		when(page.deferred).defer.then_return(None)
		expect(page.deferred).defer(page.task_extract_content, *any_args, **any_kwargs).twice()

		p = new_page()
		p.update(force=True)
		self.assertTrue(p.pending)

	def test_should_render_as_html(self):
		url = 'http://my_url/base_path/resource'
		p = Page(url=url, owner=a_user)
		p._content = '<body>b</body>'
		self.assertEqual(p.html.strip(), '<body>b</body>')

	def test_rendered_page_should_not_include_unparseable_html(self):
		url = 'http://my_url'
		orig_html = '<title>t</title><body>b<scr + ipt /></body>'

		p = new_page(orig_html, url=url)
		p.error('unparseable')
		html = p.html
		self.assertTrue('an error occurred' in html, html)
		self.assertFalse(orig_html in html, html)

	def test_should_have_host_attributes(self):
		p = new_page('<body><p>woo!</p></body>', url='http://google.com/some/page')
		self.assertEqual(p.host, 'google.com')

	def test_should_have_base_href_attribute(self):
		def assert_base(url, expected_base):
			self.assertEqual(new_page(content='', url=url).base_href, expected_base)

		assert_base('http://localhost/aa/bbbb/c', 'http://localhost/aa/bbbb/')
		assert_base('http://localhost/aa', 'http://localhost/')
		assert_base('http://localhost/', 'http://localhost/')
		assert_base('http://localhost', 'http://localhost/')

def new_page(content=None, url=some_url):
	#TODO: clean up usages of this - what is content for?
	p = page.Page(url=url, owner=a_user)
	if content is not None:
		p._raw_content = content
	p.put()
	return p

def stub_result(content, status_code=200):
	result = mock('result').with_children(status_code=status_code, content=content)
	when(page).fetch.then_return(result)
	return result


