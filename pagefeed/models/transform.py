import traceback
import re
from logging import debug, info, warning
from google.appengine.ext import db
from google.appengine.api import users
from google.appengine.ext.db.polymodel import PolyModel

from pagefeed.lib.selector import apply_selector
from pagefeed.lib.BeautifulSoup import BeautifulSoup
from pagefeed.view_helpers import view
from pagefeed.lib.url_helpers import absolute_url
from base import BaseModel

class TransformError(RuntimeError):
	pass

class Transform(PolyModel, BaseModel):
	latest_version = 1
	version = db.IntegerProperty(default=latest_version)
	host_match = db.StringProperty(required=True)
	selector = db.StringProperty(required=True)
	owner = db.UserProperty(required=True)
	name = db.StringProperty(required=True)
	
	required_properties = ('host_match', 'selector', 'owner', 'name')
	
	def put(self, *a, **k):
		if type(self) == Transform:
			raise TypeError("expected a subclass of Transform, got Transform itself")
		super(Transform, self).put(*a, **k)
	
	@classmethod
	def create(cls, action, **kwargs):
		return cls.valid_actions[action](**kwargs)

	def apply(self, page, soup):
		raise TypeError("base Transform class is never supposed to be applied")
	
	@classmethod
	def find_all(cls, user, host=None):
		q = db.Query(cls).filter('owner', user)
		if host is not None:
			q.filter('host_match', host)
		q.order('host_match').order('name')
		return q

	@classmethod
	def apply_transform(cls, transform, page, soup):
		debug("applying transform %s to page at url: %s" % (transform, page.url))
		try:
			return transform.apply(page, soup)
		except StandardError, e:
			errmsg = "transform %s failed: %s" % (type(transform).__name__, e)
			page.error(errmsg)
			info(errmsg)
			info(traceback.format_exc())
			raise TransformError(errmsg)
	
	@classmethod
	def process(cls, page):
		transforms = list(cls.find_all(user=page.owner, host=page.host))
		soup = None
		for transform in transforms:
			if soup is None:
				soup = BeautifulSoup(page.raw_content)
			soup = cls.apply_transform(transform, page, soup)
	
class FollowTransform(Transform):
	desc = "follow link"
	def apply(self, page, soup):

		links = apply_selector(soup, self.selector)
		if len(links) < 1:
			raise TransformError("no links found")
		url = links[0]['href']
		url = absolute_url(url, "http://" + page.host)
		info("replacing with contents from: %s" % (url,))
		page.use_content_url(url)


Transform.valid_actions = {
	'follow': FollowTransform,
}
