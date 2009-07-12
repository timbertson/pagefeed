from pagefeed.test.helpers import *
from models import page, Transform

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
	
	def test_should_fall_back_to_a_default_title(self):
		stub_result("<html><body>no title...</body></html>")
		p = new_page()
		self.assertEqual(p.title, page.DEFAULT_TITLE)
		self.assertTrue("no title..." in p.content)
		self.assertFalse(p.errors)

	def test_should_fall_back_to_the_whole_html_if_it_has_no_body(self):
		html = "<html><title>no body</title></html>"
		stub_result(html)
		p = new_page()
		self.assertEqual(p.title, 'no body')
		self.assertEqual(p.content, html)
		self.assertFalse(p.errors)

	def test_should_try_stripping_out_script_tags_on_unparseable(self):
		html = """<html>
			<script>
				</scr + ipt>
			</script>
			<body>caf\xc3\xa9</body>""" # note the utf-8 "acute accented e"
		stub_result(html)
		p = new_page()
		self.assertEqual(p.content, u'<body>caf\xe9</body>') # correctly unicode'd
		self.assertFalse(p.errors)

	def test_should_just_use_ascii_converted_html_on_completely_unparseable(self):
		ascii_html = "<html></scr + ipt>"
		bad_html = ascii_html + "\xd5"
		stub_result(bad_html)
		p = new_page()
		self.assertEqual(p.title, page.DEFAULT_TITLE)
		self.assertEqual(p.content, ascii_html)
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
		initial_soup = mock_on(page.Page).soup
		intermediate_soup = mock('initial_soup')
		final_soup = mock('final_soup')

		mock_on(Transform).find_all_for_user_and_host.with_(a_user, 'sub.localhost.com').is_expected.returning(filters)
		filter1.expects('apply').with_(initial_soup.raw).returning(intermediate_soup.raw)
		filter2.expects('apply').with_(intermediate_soup.raw).returning(final_soup.raw)
		final_soup.expects('__str__').returning('final content')
		
		mock_on(page).fetch.returning(mock('fetched page').with_children(status_code=200, content='some stuff').raw)
		p.put()
		self.assertEqual(p.content, 'final content')

	def test_should_update_url(self):
		p = new_page(content='initial content')
		new_url = 'http://new_url'
		response = mock('response').with_children(status_code=200, content='new content')
		mock_on(page).fetch.is_expected.with_(new_url).returning(response.raw)
		p.replace_url(new_url)
		self.assertEqual(p.url, new_url)
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

	@pending("no force argument yet")
	def test_should_retry_a_successful_download_on_update_if_forced(self):
		stub_result('')
		mock_on(page).fetch.is_expected.twice

		p = new_page()
		p.update(force=True)

	def test_should_render_as_html(self):
		url = 'http://my_url/base_path/resource'
		p = new_page('<title>t</title><body>b</body>', url=url)
		self.assertEqual(p.html.strip(),
			'<base href="http://my_url/base_path/" />\n<body>b</body>')

	def test_should_render_as_html_with_errors(self):
		url = 'http://my_url'
		orig_html = '<title>t</title><body>b<scr + ipt /></body>'

		p = new_page(orig_html, url=url)
		html = p.html
		self.assertTrue('An error occurred' in html, html)
		self.assertTrue(orig_html in html, html)

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

def new_page(content=None, url='http://localhost/dontcare'):
	p = page.Page(url=url, owner=a_user)
	if content is None:
		p.put()
	else:
		p.populate_content(content)
	return p

def stub_result(content, status_code=200):
	result = mock('result').with_children(status_code=status_code, content=content)
	mock_on(page).fetch.returning(result.raw)


