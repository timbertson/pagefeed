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

class TransformError(RuntimeError):
	pass

class Transform(PolyModel, BaseModel):
	host_match = db.TextProperty(required=True)
	selector = db.StringProperty(required=True)
	owner = db.UserProperty(required=True)
	index = db.IntegerProperty()
	name = db.StringProperty(required=True)
	
	@staticmethod
	def create(action, **kwargs):
		actionClasses = {'follow':FollowTransform}
		return actionClasses[action](**kwargs)

	def apply(self, soup):
		pass
	
	@classmethod
	def find_all(cls, user, host=None):
		q = db.Query(cls).filter('owner', user)
		if host is not None:
			info("applying filter host = %s" % (host,))
			q.filter('host_match', host)
		else:
			info("no host filter")
		q.order('host_match')
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
		transforms = cls.find_all(user=page.owner, host=page.host)
		transforms = cls._monkeypatch_dzone(page, transforms)
		[cls.apply_transform(transform, page) for transform in transforms]
	
	@classmethod
	def _monkeypatch_dzone(cls, page, transforms): #FIXME: !!!
		if transforms: return transforms
		dzone = 'dzone.com'
		if page.host.endswith(dzone) and users.is_current_user_admin():
			debug("monkeypatching dzone transformer...")
			transforms = [FollowTransform(owner=page.owner, host_match=dzone)]
		return transforms


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


