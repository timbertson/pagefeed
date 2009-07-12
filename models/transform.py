from google.appengine.ext import db

from logging import debug, info, warning
from helpers import view
from base import BaseModel

class ActionProperty(db.StringProperty):
	pass # don't do validation for now

class Transform(BaseModel):
	host_match = db.TextProperty(required=True)
	action = ActionProperty()
	selector = db.StringProperty()
	owner = db.UserProperty(required=True)
	index = db.IntegerProperty()
	
	def apply(self, soup):
		return soup
	
	@classmethod
	def find_all_for_user_and_host(cls, owner, host):
		return db.Query(cls).filter('owner =', owner).filter('host_match =', host).order('index').fetch(limit=50)
	
	@staticmethod
	def apply_all(filters, inital):
		result = inital
		for filter_ in filters:
			result = filter_.apply(result)
		return result
	
	@classmethod
	def process(cls, page):
		filters = cls.find_all_for_user_and_host(page.owner, page.host)
		return cls.apply_all(filters, page.soup)


class FollowTransform(Transform):
	name = "follow link"
	def apply(self):
		pass

class DeleteTransform(Transform):
	name = "remove items"
	def apply(self):
		pass
	
class SelectTransform(Transform):
	name = "select subsets of page"
	def apply(self):
		pass
	
