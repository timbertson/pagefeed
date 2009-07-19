from test_helpers import *
from pagefeed.models import transform
from lib.BeautifulSoup import BeautifulSoup as b_soup

class TransformTest(TestCase):
	def tearDown(self):
		for trans in transform.Transform.all():
			trans.delete()

	def test_should_create_the_appropriate_model(self):
		orig_follow = transform.Transform.create(action='follow', selector='foo', host_match='bar', owner=fixtures.a_user, name='blah')
		orig_follow.put()
		follows = transform.Transform.all().fetch(2)
		self.assertEqual(len(follows), 1)
		follow = follows[0]
		self.assertEqual(type(follow), transform.FollowTransform)
		self.assertEqual(follow.selector, 'foo')
		self.assertEqual(follow.host_match, 'bar')
		self.assertEqual(follow.name, 'blah')
		self.assertEqual(follow.owner, fixtures.a_user)

	@ignore
	def test_should_assign_index_automatically(self):
		pass

	def test_should_find_transforms_based_on_owner(self):
		kw = dict(action='follow', selector='foo', name='foo')
		transform.Transform.create(host_match='xyz', owner=fixtures.a_user, **kw).put()
		transform.Transform.create(host_match='bar', owner=fixtures.a_user, **kw).put()

		self.assertEqual(len(transform.Transform.find_all(user=fixtures.a_user)), 2)
		self.assertEqual(len(transform.Transform.find_all(user=fixtures.another_user)), 0)

	@ignore("needs transform equality")
	def test_should_find_transforms_based_on_host_and_owner(self):
		orig_follow = transform.Transform.create(action='follow', selector='foo', host_match='bar', owner=fixtures.a_user, name='foo')
		orig_follow.put()
		
		follows = transform.FollowTransform.find_all(user=fixtures.a_user, host='bar')
		print repr(list(transform.FollowTransform.find_all(user=fixtures.a_user)))
		self.assertEqual(len(follows), 1)
		self.assertEqual(orig_follow, follows[0])

	def test_should_follow_url_for_follow_action(self):
		selector = "div[class=content]|a[1]"
		xform = transform.FollowTransform(owner=fixtures.a_user, selector=selector, host_match='localhost', name='blah')
		html = """
			<body>
				<div class="content">
					<a href="http://not_this">blah</a>
					<a href="http://linked_url">blah</a>
					<a href="http://or_this">blah</a>
				</div>
			</body>
			"""
		page = mock('page').with_children(soup=b_soup(html), host='')
		page.expects('replace_with_contents_from').with_('http://linked_url')
		xform.apply(page.raw)

	@ignore
	def test_should_not_follow_url_when_selection_fails(self):
		selector = "div[class=content]|a[1]"
		xform = Transform(owner=fixtures.a_user, action='follow', selector=selector, host_match='localhost')
		html = """
			<body>
				<div class="not_content">
					<a href="http://not_this">blah</a>
				</div>
			</body>
			"""
		page = mock('page').with_children(soup=b_soup())
		page.does_not_expect('replace_link')
		page.expects("info").with_("FollowTransform: couldn't find any items matching `%s`"  % (selector,))
		xform.apply(page)

class SelectorTest(TestCase):
	def assertExtraction(self, content, selector, expected_results):
		soup = b_soup(content)
		results = transform.apply_selector(soup, selector)
		string_results = map(str, results)
		self.assertEqual(string_results, expected_results)

	def test_should_apply_a_complex_selector(self):
		selector="div[class=the_class]|[0]|p[2],a"
		html = """
			<div class="something else" />
			<div class="the_class">
				<p>zero</p>
				<p>one</p>
				<p>two</p>
				<a>link1</a>
			</div>
			<a>link2</a>
			"""
		self.assertExtraction(html, selector,
			["<p>two</p>", "<a>link1</a>", "<a>link2</a>"])

	def test_should_select_on_presence_of_attribute(self):
		html = """
			<div>not here</div>
			<div class="present">here</div>
			"""
		self.assertExtraction(html, "div[class]",
			['<div class="present">here</div>'])

	def test_should_select_on_presence_of_attribute_without_tag(self):
		html = """
			<div>not here</div>
			<div class="present">here</div>
			"""
		self.assertExtraction(html, "[class=present]",
			['<div class="present">here</div>'])

	def test_should_select_index(self):
		html = """
			<div>0</div>
			<div>1</div>
			"""
		self.assertExtraction(html, "div[0],div[-2]",
			['<div>0</div>', '<div>0</div>'])
		
	def test_should_select_subnode_and_attribute(self):
		html = """
			<div>-1</div>
			<div class="x">0</div>
			<div class="y">1</div>
			"""
		self.assertExtraction(html, "div[class]|[0]",
			['<div class="x">0</div>'])

	def test_should_select_multiple_items(self):
		html = """
			<div>0</div>
			<div>1</div>
			<p>
				<b>bold</b>
			</p>
			"""
		self.assertExtraction(html, "div,b",
			['<div>0</div>', '<div>1</div>', '<b>bold</b>'])


