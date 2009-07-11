from pagefeed.test.helpers import *
from models import Transform
from pagefeed.test import fixtures

class TransformTest(TestCase):
	@ignore
	def test_should_follow_url_for_follow_action(self):
		xpath = "//div[@class='content']//a[1]"
		xform = Transform(owner=fixtures.a_user, action='follow', selector=xpath, host_match='localhost')
		page = mock('page')
		link = mock('link').with_children(href='linked url')
		page.expects('get_xpath').with_(xpath).returning(link)
		page.expects('replace_link').with_('linked url')
		xform.apply(page)


