import operator
from base import BaseModel
from google.appengine.ext import db
from datetime import datetime, timedelta


class Content(BaseModel):
	latest_version = 0
	version = db.IntegerProperty(default=latest_version)
	min_size = 2048 # characters
	url = db.URLProperty(required=True)
	title = db.StringProperty()
	body = db.TextProperty()
	source = db.StringProperty()
	lastmod = db.DateTimeProperty(auto_now_add=True)

	def __repr__(self):
		return "<Content (%s) for %s: title=%r, length=%s, time=%s>" % (
			self.source, self.url, self.title, self.get_size(), self.lastmod)

	def __cmp__(self, other):
		from pagefeed.content_extraction import VIEWTEXT
		both = (self, other)
		self_is_better = 1
		other_is_better = -1

		# viewtext is so awesome that we always prefer it as long
		# as it exceeds the minimum size
		viewtext_preference = 0
		if self.source != other.source:
			for item, result in [(self, self_is_better), (other, other_is_better)]:
				if item.source == VIEWTEXT and not Content.too_small(item):
					return result

		# otherwise, resort to best size:
		sizes = map(Content.get_size, both)
		if operator.eq(*sizes):
			return viewtext_preference
		if any(map(Content.too_small, both)):
			# bigger is better when either is too small
			return cmp(*sizes)
		# if both are big enough, smaller is better
		return cmp(*reversed(sizes))

	def too_small(self):
		return self.size < self.min_size

	def get_size(self):
		return len(self.title or '') + len(self.body or '')
	size = property(get_size)
	
	def __nonzero__(self):
		return self.size > 0
	
	@classmethod
	def for_url(cls, url):
		return db.Query(cls).filter('url =', url).fetch(100)

	@classmethod
	def already_fetched(cls, url, source):
		return db.Query(cls).filter('url =', url).filter('source =', source).count() > 0

	@classmethod
	def trash(cls, url):
		map(db.delete, cls.for_url(url))

	@classmethod
	def purge(cls):
		one_day_ago = datetime.utcnow() - timedelta(days=1)
		q = db.Query(cls, keys_only=True).filter('lastmod <', one_day_ago)
		for item in q:
			db.delete(item)




