import cgi
from mocktest import *

from models.page import Page
from models.user import UserID
from pagefeed.test import fixtures

class FeedTest(TestCase):
	def get_feed(self, email, secret, **kwargs):
		email = cgi.escape(str(email))
		secret = cgi.escape(str(secret))
		return fixtures.app().get('/feed/%s-%s/' % (secret, email), **kwargs)
		
	def test_should_display_feeds_for_a_user(self):
		email = fixtures.a_user.email()
		userid = UserID.get(email)
		page = fixtures.stub_page()
		page.title = 'the title!'
		mock_on(Page).find_all.is_expected.with_(fixtures.a_user)
		response = self.get_feed(email, userid.handle)
		response.mustcontain('the title!')

	def test_should_not_display_feeds_for_an_illegitimate_user(self):
		email = fixtures.a_user.email()
		userid = UserID.get(email)
		mock_on(Page).find_all.is_not_expected
		self.get_feed(email, '123', status=403)

