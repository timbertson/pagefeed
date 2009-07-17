import traceback
import re
from logging import debug, info, warning
from google.appengine.ext import db
from google.appengine.api import users
from google.appengine.ext.db.polymodel import PolyModel

from lib.selector import apply_selector
from helpers import view, absolute_url
from base import BaseModel

class TransformError(RuntimeError):
	pass

class ActionProperty(db.StringProperty):
	pass # don't do validation for now

class Transform(PolyModel, BaseModel):
	host_match = db.StringProperty(required=True)
	selector = db.StringProperty(required=True)
	owner = db.UserProperty(required=True)
	name = db.StringProperty(required=True)
	
	
	required_properties = ('host_match', 'action', 'selector', 'owner', 'name')
	
	def put(self, *a, **k):
		if type(self) == BaseModel:
			raise TypeError("expected a subclass of BaseModel, got %s" % (BaseModel,))
		super(Transform, self).put(*a, **k)
	
	@classmethod
	def create(cls, action, **kwargs):
		return cls.valid_actions[action](**kwargs)

	def apply(self, soup):
		raise TypeError("base Transform class is never supposed to be applied")
	
	@classmethod
	def find_all(cls, user, host=None):
		q = db.Query(cls).filter('owner', user)
		if host is not None:
			info("applying filter host = %s" % (host,))
			q.filter('host_match', host)
		else:
			info("no host filter")
		q.order('host_match').order('name')
		return q.fetch(limit=50)

	@classmethod
	def apply_transform(cls, transform, page):
		debug("applying transform %s to page at url: %s" % (transform, page.url))
		try:
			transform.apply(page)
		except RuntimeError, e:
			errmsg = "transform %s failed: %s" % (type(transform).__name__, e)
			info(errmsg)
			info(traceback.format_exc())
			raise TransformError(errmsg)
	
	@classmethod
	def process(cls, page):
		for transform in cls.find_all(user=page.owner, host=page.host):
			cls.apply_transform(transform, page)
	
class FollowTransform(Transform):
	desc = "follow link"
	def apply(self, page):
		links = apply_selector(page.soup, self.selector)
		if len(links) < 1:
			raise TransformError("no links found")
		url = links[0]['href']
		url = absolute_url(url, "http://" + page.host)
		info("replacing with contents from: %s" % (url,))
		page.replace_with_contents_from(url)


Transform.valid_actions = {
	'follow': FollowTransform,
}
