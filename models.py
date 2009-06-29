from google.appengine.ext import db
from google.appengine.ext.db import Model
from google.appengine.api.urlfetch import fetch, DownloadError

import re
import htmllib

def unescape_html(s):
	p = htmllib.HTMLParser(None)
	p.save_bgn()
	p.feed(s)
	return p.save_end()


class Page(Model):
	url = db.URLProperty(required=True)
	content = db.TextProperty()
	title = db.StringProperty()
	error = db.BooleanProperty()
	owner = db.UserProperty(required=True)
	date = db.DateTimeProperty(auto_now_add=True)
	
	@staticmethod
	def _get_title(content):
		match = re.compile(r'<title>([^<]+)</title>', re.DOTALL)
		matched = match.search(content)
		if matched:
			return unescape_html(matched.group(1))
		return '[pagefeed saved item]'
	
	@staticmethod
	def _get_body(content):
		match = re.compile(r'<body(?: [^>]*)?>(.*)</body>', re.DOTALL)
		matched = match.search(content)
		if matched:
			return matched.group(1)
		return content
	
	def fetch(self):
		try:
			response = fetch(self.url)
			if response.status_code >= 400:
				raise DownloadError("status code %s\n%s" % (response.status_code, response.content))
			content = response.content.decode('UTF-8')
			self.content = self._get_body(content)
			self.title = self._get_title(content)
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

class UserID(Model):
	user = db
	email = db.EmailProperty(required=True)
	handle = db.IntegerProperty(required=True)
	
	@staticmethod
	def _new_handle(email):
		import time
		import random
		random.seed((time.clock() * (1 << 32)) + hash(email))
		return random.getrandbits(60)
	
	@classmethod
	def get(cls, email):
		user = db.Query(cls).filter('email =', email).get()
		if not user:
			handle = cls._new_handle(email)
			user = cls(email=email, handle=handle)
			user.put()
		return user

	@classmethod
	def auth(cls, email, handle):
		user = db.Query(cls).filter('email =', email).filter('handle =', handle).get()
		return user is not None


