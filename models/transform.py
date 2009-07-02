from google.appengine.ext import db

from logging import debug, info, warning
from helpers import view

class ActionProperty(db.StringProperty):
	pass # don't do validation for now

class Transform(db.Model):
	host_match = db.TextProperty(required=True)
	action = ActionProperty()
	selector = db.StringProperty()
	owner = db.UserProperty(required=True)
	index = db.IntegerProperty()
	
	def apply(self, soup):
		return soup
	
	@classmethod
	def find_all_for_user_and_host(cls, user, host):
		pass
	
	@staticmethod
	def apply_all(filters, inital):
		result = inital
		for filter_ in filters:
			result = filter_.apply(result)
		return result
	
	@classmethod
	def process(cls, user, page):
		filters = cls.find_all_for_user_and_host(user, page.host)
		cls.apply_all(filters, page.soup)


