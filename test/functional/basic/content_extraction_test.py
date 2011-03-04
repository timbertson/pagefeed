from test_helpers import *
from pagefeed.models import page

class ContentExtractionTest(object):
	def test_should_add_a_new_page_without_content():
		pass

	def test_should_trigger_a_cron_task_for_extraction():
		pass
	
	def test_should_fetch_article_from_viewtext():
		pass
	
	def test_should_fetch_article_directly():
		pass

	def test_should_treat_failed_fetches_as_None_content():
		pass

	def test_should_accept_the_shortest_result_over_a_certain_size():
		pass

	def test_should_mark_content_as_requiring_fetch_again():
		pass

	def test_should_not_appear_in_RSS_until_content_has_been_fetched():
		pass
