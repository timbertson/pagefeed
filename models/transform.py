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
		pass
	
	@classmethod
	def find_all_for_user_and_host(cls, owner, host):
		return db.Query(cls).filter('owner =', owner).filter('host_match =', host).order('index').fetch(limit=50)
	
	@classmethod
	def process(cls, page):
		filters = cls.find_all_for_user_and_host(page.owner, page.host)
		[filter_.apply(page) for filter_ in filters]

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
	
