from test_helpers import *
from models import page, Transform
from models.page import Page

some_url = 'http://localhost/dontcare'

class PageLifecycleTest(TestCase):
	def setUp(self):
		super(PageLifecycleTest, self).setUp()
		self.defer_mock = mock(page.deferred).defer

	def test_page_should_start_with_no_content(self):
		p = Page(url=some_url, owner=a_user)
		self.assertEquals(p.content, None)
		self.assertNotNone(p.key())
	
	def test_page_creation_should_launch_a_task_to_fetch_data(self):
		p = Page(url=some_url, owner=a_user)
		expect(defer_mock).defer.once().with_args(page.fetch_raw_content, p.key())

	def test_fetch_data_should_launch_content_extraction_tasks(self):
		extractor1, extractor2 = mock(), mock()
		modify(page).content_extractors = [extractor1, extractor2]

		p = Page(url=some_url, owner=a_user)

		expect(page.Transform).process(p)
		expect(self.defer_mock).defer(extractor1, p.key())
		expect(self.defer_mock).defer(extractor2, p.key())
		expect(self.defer_mock).defer(page.store_best_content, p.key())

		p.fetch_content()
	
	def test_should_log_error_and_ignore_transforms_if_they_fail(self):
		modify(page).content_extractors = []

		p = Page(url=some_url, owner=a_user)

		expect(page.transform).process(p).and_raise(TransformError("transform failed"))
		expect(p).error("transform failed")

		p.fetch_content()
		self.assertTrue(p.transformed)
	
	def test_reset_should_clear_all_content(self):
		p = Page(url=some_url, owner=a_user)
		p.content = "content!"
		p.raw_content = "raw content!"
		p.title = "title"
		
		p.update(force=True)
		self.assertNone(p.content)
		self.assertNone(p.raw_content)
		self.assertEqual(p.title, "[localhost saved item]")

	def test_store_best_content_should_do_nothing_if_not_all_processors_have_completed(self):
		p = Page(url=some_url, owner=a_user)
		replace(page).content_extractors = [1,2,3,4,5]
		page.store_best_content(p.key())
		when(Content).for_url(p.url).then_return([1,2,3,4])

		expect(page).set_content(p.key(), anything).never()
		page.store_best_content(p.key(), 1)

	def test_store_best_content_should_do_so_if_all_extractors_are_complete(self):
		p = Page(url=some_url, owner=a_user)
		replace(page).content_extractors = [1,2,3,4,5]
		page.store_best_content(p.key())
		when(Content).for_url(p.url).then_return([1, 6, 10, 8, 4])

		expect(page).set_content(p.key(), 10)
		page.store_best_content(p.key())

class PageTest(TestCase):
	def test_should_load_well_formed_page(self):
		content = """
			<html>
			<title>the title!</title>
			<body>the body!</body>
			</html>
			"""
		result = mock('result').with_children(status_code=200, content=content)
		url = 'http://localhost/some/path'
		mock_on(page).fetch.is_expected.with_(url).returning(result.raw)
		
		p = new_page(url=url)
		self.assertEqual(p.title, 'the title!')
		self.assertEqual(p.content, '<body>the body!</body>')
		self.assertFalse(p.errors)
		
	def test_should_omit_page_fragment_from_request(self):
		result = mock('result').with_children(status_code=200, content='blah')
		url = 'http://localhost/some/path'
		full_url = url + "#anchor"
		mock_on(page).fetch.is_expected.with_(url).returning(result.raw)
		
		p = new_page(url=full_url)
		self.assertEqual(p.url, full_url)
		self.assertEqual(p.content, 'blah')
		self.assertFalse(p.errors)
		

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
		result = mock('result').with_children(status_code=200, content=content)
		url =      'http://localhost/some/path/to_page.html'
		rel_base = "http://localhost/some/path/"
		base =     "http://localhost/"
		mock_on(page).fetch.is_expected.with_(url).returning(result.raw)
		
		p = new_page(url=url)
		self.assertFalse(p.errors)
		print p.content
		self.assertTrue('<a href="%srel.html">' % rel_base in p.content)
		self.assertTrue('<a href="%spath/to/pathed.html">' % base in p.content)
		self.assertTrue('<a href="http://google.com/abs.html">' in p.content)
		self.assertTrue('<img src="%spath/to/path2.jpg" />' % base in p.content)

	def test_should_remove_a_bunch_of_unwanted_html_attributes(self):
		stub_result("""
				<html>
					<p style="border-color:#ff; background:#fff;" COLOR="foo" alt="lala">
						<img src="http://localhost/blah" width  =  100 height=  20px />
						<div bgcolor=foo>
							so then style=none should not be stripped
							<span bgcolor-andthensome="not_strippped"></span>
						</div>
					</p>
				</html>
			""")
		p = new_page()
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
		print "ACTUAL: " + p.content
		print '-----'
		print "EXPECTED: " + expected_html
		self.assertEqual(p.content.strip().replace('\t',''), expected_html.strip().replace('\t',''))
	
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

	def test_should_fall_back_to_entire_html_if_it_has_no_body(self):
		html = "<html><title>no body</title></html>"
		stub_result(html)
		p = new_page()
		self.assertEqual(p.title, 'no body')
		self.assertEqual(p.content, html)
		self.assertFalse(p.errors)


	def test_should_discard_html_on_completely_unparseable(self):
		html = "<html></scr + ipt>"
		stub_result(html)
		p = new_page()
		self.assertEqual(p.content, '')
		self.assertTrue(p.errors)
	
	def test_should_strip_out_script_and_style_and_link_tags(self):
		html = "<html><body><script></script><style></style><link /></body>"
		stub_result(html)
		p = new_page()
		self.assertEqual(p.content, "<body></body>")
		self.assertFalse(p.errors)
	
	def test_should_apply_all_matching_transforms(self):
		filter1 = mock('filter1')
		filter2 = mock('filter2')
		filters = [filter1.raw, filter2.raw]

		p = page.Page(owner=a_user, url='http://sub.localhost.com/some/path/to/file.html')
		response = mock('response').with_children(status_code=200, content='initial content')
		mock_on(page).fetch.returning(response.raw)

		mock_on(Transform).find_all.with_(user=a_user, host='sub.localhost.com').is_expected.returning(filters)
		filter1.expects('apply').with_(p)
		filter2.expects('apply').with_(p)
		
		p.put()

	def test_should_fetch_content_from_new_url(self):
		old_url = 'http://old_url'
		new_url = 'http://new_url'
		p = new_page(content='initial content', url=old_url)

		response = mock('response').with_children(status_code=200, content='new content')
		mock_on(page).fetch.is_expected.with_(new_url).returning(response.raw)
		p.replace_with_contents_from(new_url)

		self.assertEqual(p.url, old_url)
		self.assertEqual(p.content, 'new content')
	
	@ignore
	def test_should_extract_xpath_elements(self):
		pass
	
	def test_should_note_an_error_when_download_fails(self):
		stub_result('', status_code = 400)
		p = new_page()
		self.assertTrue(p.errors)

	def test_should_retry_a_failed_download_on_update(self):
		stub_result('', status_code=404)
		mock_on(page).fetch.is_expected.twice

		p = new_page()
		p.update()

	def test_should_not_retry_a_successful_download_on_update(self):
		stub_result('')
		mock_on(page).fetch.is_expected.once

		p = new_page()
		p.update()

	@ignore
	def test_should_update_date_on_fetch(self):
		pass

	def test_should_retry_a_successful_download_on_update_if_forced(self):
		stub_result('')
		mock_on(page).fetch.is_expected.twice

		p = new_page()
		p.update(force=True)

	def test_should_render_as_html(self):
		url = 'http://my_url/base_path/resource'
		p = new_page('<title>t</title><body>b</body>', url=url)
		self.assertEqual(p.html.strip(), '<body>b</body>')

	def test_rendered_page_should_not_include_unparseable_html(self):
		url = 'http://my_url'
		orig_html = '<title>t</title><body>b<scr + ipt /></body>'

		p = new_page(orig_html, url=url)
		html = p.html
		self.assertTrue('an error occurred' in html, html)
		self.assertFalse(orig_html in html, html)

	def test_should_have_soup_and_host_attributes(self):
		p = new_page('<body><p>woo!</p></body>', url='http://google.com/some/page')
		self.assertEqual(p.host, 'google.com')
		self.assertEqual(p.soup.body.p.string, 'woo!')

	def test_should_have_base_href_attribute(self):
		def assert_base(url, expected_base):
			self.assertEqual(new_page(content='', url=url).base_href, expected_base)

		assert_base('http://localhost/aa/bbbb/c', 'http://localhost/aa/bbbb/')
		assert_base('http://localhost/aa', 'http://localhost/')
		assert_base('http://localhost/', 'http://localhost/')
		assert_base('http://localhost', 'http://localhost/')

	def test_should_accept_multiline_titles(self):
		p = new_page("<title>foo\nbar</title>")
		self.assertEqual(p.title, "foo bar")


def new_page(content=None, url=some_url):
	p = page.Page(url=url, owner=a_user)
	if content is None:
		p.put()
	else:
		p.populate_content(content)
	return p

def stub_result(content, status_code=200):
	result = mock('result').with_children(status_code=status_code, content=content)
	mock_on(page).fetch.returning(result.raw)
	return result


