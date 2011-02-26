import operator
from base import BaseModel
from google.appengine.ext import db

class Content(BaseModel):
	min_size = 1000 # characters
	url = db.URLProperty(required=True)
	title = db.StringProperty()
	body = db.TextProperty()
	source = db.StringProperty()

	def __cmp__(self, other):
		both = (self, other)
		sizes = map(Content.get_size, both)
		if operator.eq(*sizes):
			return 0
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
		return db.Query(cls).filter('url =', url).get()

	@classmethod
	def already_fetched(cls, url, source):
		return db.Query(cls).filter('url =', url).filter('source =', source).count() > 0

	@classmethod
	def trash(cls, url):
		map(db.delete, cls.for_url(url))



