from mocktest import *

from models.page import Page
from models.user import UserID
from user import a_user

class FeedTest(TestCase):
	def test_should_display_feeds_for_a_user(self):
		mock_on(page).find_all.is_expected.with_()#TODO

