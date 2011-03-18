from pagefeed.models import Content
from test_helpers import *

some_url = 'http://example.com'
some_title = 'some title'

class TestContentComparison(TestCase):
	def test_should_compare_a_list_of_contents(self):
		contents = [
				self.content_of_length(1),
				self.content_of_length(4),
				self.content_of_length(8),
				self.content_of_length(10),
				self.content_of_length(4),
				self.content_of_length(9)]
		self.assertEquals(max(contents).size, 10)

	def test_should_prefer_nonempty_content(self):
		self.assertEquals(cmp(self.empty_content(), self.content_of_length(1)), -1)

	def test_should_prefer_viewtext_as_long_as_it_is_above_the_minimum_size(self):
		non_viewtext = self.content_big_enough_by(1)
		viewtext = self.content_big_enough_by(100)
		viewtext.source = 'viewtext'
		self.assertEquals(max(viewtext, non_viewtext), viewtext)

	def test_should_prefer_bigger_content_when_both_are_below_minimum_size(self):
		self.assertEquals(cmp(self.content_too_small_by(1), self.content_too_small_by(100)), 1)

	def test_should_prefer_bigger_content_when_either_is_below_minimum_size(self):
		self.assertEquals(cmp(self.content_too_small_by(1), self.content_big_enough_by(1)), -1)

	def test_should_prefer_smaller_content_when_both_are_above_minimum_size(self):
		self.assertEquals(cmp(self.content_big_enough_by(1), self.content_big_enough_by(10)), 1)

	def test_should_not_prioritise_content_with_equal_lengths(self):
		self.assertEquals(cmp(self.content_big_enough_by(1), self.content_big_enough_by(1)), 0)

	def content_too_small_by(self, n):
		body = 'a' * (Content.min_size - n - len(some_title))
		content = Content(url=some_url, title=some_title, body=body)
		self.assertEquals(content.size, Content.min_size - n)
		self.assertTrue(content.too_small())
		return content

	def content_big_enough_by(self, n):
		body = 'a' * (Content.min_size + n - len(some_title))
		content = Content(url=some_url, title=some_title, body=body)
		self.assertEquals(content.size, Content.min_size + n)
		self.assertFalse(content.too_small())
		return content

	def empty_content(self):
		content = Content(url=some_url)
		self.assertEquals(content.size, 0)
		return content

	def content_of_length(self, n):
		content = Content(url=some_url, body='x' * n)
		self.assertEquals(content.size, n)
		return content

