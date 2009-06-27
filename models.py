from google.appengine.ext import db
from google.appengine.ext.db import Model
from google.appengine.api.urlfetch import fetch, DownloadError

class Page(Model):
	url = db.URLProperty()
	content = db.TextProperty()
	error = db.BooleanProperty()
	owner = db.UserProperty()
	date = db.DateTimeProperty(auto_now_add=True)
	
	def fetch(self):
		try:
			response = fetch(self.url)
			if response.status_code >= 400:
				raise DownloadError("status code %s\n%s" % (response.status_code, response.content))
			self.content = response.content
			self.error = False
		except DownloadError, e:
			self.error = True
			self.content = e.message
	
	def update(self):
		if self.error:
			self.fetch()
			if not self.error:
				self.save()
	
	def put(self, *a, **k):
		if not self.content:
			self.fetch()
		super(type(self), self).put(*a,**k)

	@classmethod
	def find_all(cls, owner, limit=50):
		return db.Query(cls).filter('owner =', owner).order('-date').fetch(limit=limit)
	
	@classmethod
	def find(cls, owner, url):
		return db.Query(cls).filter('owner =', owner).filter('url =', url).get()
		
