import urllib2
from google.appengine.api import users

from pagefeed.models import Page, UserID

from test_helpers import *

class RootTest(TestCase):
	def setUp(self):
		self.page = PageDriver()
	
	def test_should_show_page_list_for_a_logged_in_user(self):
		page = fixtures.stub_page()
		response = fixtures.app().get('/')
		
		response.mustcontain('Welcome to PageFeed, foo')
		response.mustcontain(page.title)
	
	def test_should_link_to_feed_for_a_logged_in_user(self):
		page = fixtures.stub_page()
		response = fixtures.app().get('/')
		
		response.mustcontain(page.title)

		user = fixtures.a_user
		email = user.email()
		user_handle = UserID.get(email).handle
		
		feed_link = '/feed/%s-%s/' % (user_handle, urllib2.quote(email))
		content = response.body
		response.mustcontain('<link href="%s" type="application/rss+xml"' % (feed_link))
		response.mustcontain('<a href="%s"' % feed_link)
	
	def test_should_delete_items_and_redirect_to_root(self):
		page = fixtures.stub_page()
		response = fixtures.app().get('/')
		forms = response.forms
		delete_form = forms['delete_page_%s' % (page.key())]

		def check(owner, url):
			self.assertEqual(url, page.url)
			return page
			
		expect(Page).find.and_call(check)
		expect(page).delete()

		response = delete_form.submit().follow()
		self.assertEqual(response.request.url, 'http://localhost/')
		
	def test_should_update_items_and_redirect_to_root(self):
		page = fixtures.stub_page()
		response = fixtures.app().get('/')
		forms = response.forms
		update_form = forms['update_page_%s' % page.key()]
		
		def check(owner, url):
			self.assertEqual(url, page.url)
			return page
			
		expect(Page).find.and_call(check)
		expect(page).update(force=True)
		
		response = update_form.submit().follow()
		self.assertEqual(response.request.url, 'http://localhost/')

class PaginationTest(TestCase):
	def setUp(self):
		self.app = fixtures.app()
		self.items_per_page = 10

		page = PageDriver()
		for x in range(0,self.items_per_page + 2):
			Page(url='http://localhost/?%s' % (x,), owner=a_user, content='some content').put()
		
		print "REALLY THERE ARE %s pages" % (len(Page.all().fetch(100)),)

	def get_page(self, p=0):
		self.response = self.app.get('/?page=%s' % (p,))
		self.soup = BeautifulSoup(self.response.body)
		
	def tearDown(self):
		[p.delete() for p in Page.all()]
	
	def all_items(self):
		return self.soup.find(attrs={'id':'links'}).findChildren('li')
	
	def pagination_links(self):
		def is_pagination(link):
			return 'pagination' in link['class']
		return filter(is_pagination, self.soup.findAll('a', attrs={'class':True}))
	
	def next_link(self):
		links = filter(lambda link: 'next' in link['class'], self.pagination_links())
		return None if len(links) == 0 else links[0]

	def prev_link(self):
		links = filter(lambda link: 'prev' in link['class'], self.pagination_links())
		return None if len(links) == 0 else links[0]
		
	def test_should_have_only_prev_link_on_the_last_page(self):
		self.get_page(1)
		self.assertEqual(self.next_link(), None)
		self.assertNotEqual(self.prev_link(), None)
	
	def test_should_have_only_next_link_on_the_first_page(self):
		self.get_page(0)
		self.assertEqual(self.prev_link(), None)
		self.assertNotEqual(self.next_link(), None)
		
	def test_should_paginate_forwards_when_there_are_more_than_a_page_worth_of_items(self):
		self.get_page()
		self.assertEqual(len(self.all_items()), self.items_per_page)
		self.assertTrue(self.next_link()['href'].endswith('/?page=1'))
		
		self.get_page(1)
		self.assertEqual(len(self.all_items()), 2)
	
	
	def test_should_paginate_backwards_when_page_is_greater_than_zero(self):
		self.get_page(1)
		self.assertEqual(len(self.all_items()), 2)
		print repr(self.prev_link())
		print repr(self.pagination_links())
		self.assertTrue(self.prev_link()['href'].endswith('/?page=0'))


