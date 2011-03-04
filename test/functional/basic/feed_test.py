import cgi
from test_helpers import *

from pagefeed.models.page import Page
from pagefeed.models.user import UserID

class FeedTest(TestCase):
	def get_feed(self, email, secret, **kwargs):
		email = cgi.escape(str(email))
		secret = cgi.escape(str(secret))
		print repr(fixtures)
		return fixtures.app().get('/feed/%s-%s/' % (secret, email), **kwargs)
		
	def test_should_display_complete_feeds_for_a_user(self):
		email = fixtures.a_user.email()
		userid = UserID.get(email)
		page = fixtures.stub_page()
		page.title = 'the title!'
		expect(Page).find_complete(fixtures.a_user).and_return([page])
		response = self.get_feed(email, userid.handle)
		print repr(response.body)
		response.mustcontain('the title!')

	def test_should_not_display_feeds_for_an_illegitimate_user(self):
		email = fixtures.a_user.email()
		expect(Page).find_all.never()
		self.get_feed(email, '123', status=403)
	
