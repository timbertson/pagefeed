from google.appengine.ext import db

from google.appengine.api.urlfetch import fetch, DownloadError
from controllers.helpers import render

from lib.BeautifulSoup import BeautifulSoup, HTMLParseError
from logging import debug, info, warning

DEFAULT_TITLE = '[pagefeed saved item]'

from helpers import view
import re

class Unparseable(ValueError):
	pass

def ascii(s):
	return s.encode('ascii', 'ignore')

class Page(db.Model):
	url = db.URLProperty(required=True)
	content = db.TextProperty()
	title = db.StringProperty()
	error = db.TextProperty()
	owner = db.UserProperty(required=True)
	date = db.DateTimeProperty(auto_now_add=True)
	
	@staticmethod
	def _get_title(soup):
		return unicode(soup.title.string or DEFAULT_TITLE)
	
	@staticmethod
	def _get_body(soup):
		return unicode(soup.body or soup)

	@staticmethod
	def _remove_script_tags(content):
		script_re = re.compile(
			'<script.*?</script[^>]*>',
			re.MULTILINE | re.IGNORECASE)
		return script_re.sub('', content)
	
	def _populate_content(self, raw_content):
		self.error = None
		try:
			soup = self._parse_content(raw_content)
			self.content = self._get_body(soup)
			self.title = self._get_title(soup)
		except Unparseable, e:
			safe_content = ascii(raw_content)
			self._failed(e.message, safe_content)
	
	@classmethod
	def _parse_content(cls, content):
		try:
			return BeautifulSoup(raw_content)
		except HTMLParseError, e:
			error("initial parsing failed: %s" % (e.message,))
			original_msg = e.message
			safe_content = ascii(raw_content)
			try:
				return BeautifulSoup(cls._remove_script_tags(safe_content))
			except HTMLParseError, e:
				error("failsafe parsing also failed: %s" % (e.message,))
				raise Unparseable(original_msg)
			

	def fetch(self):
		try:
			response = fetch(self.url)
			if response.status_code >= 400:
				raise DownloadError("request returned status code %s\n%s" % (response.status_code, response.content))
			self._populate_content(response.content)
		except DownloadError, e:
			self._failed(e.message, 'no content was downloaded')
	
	def _failed(self, error, content=''):
		debug("error: %s" % (error,))
		self.title = DEFAULT_TITLE
		self.error = error
		self.content = content
	
	def update(self):
		if self.error is not None:
			info("page %s had an error - redownloading...." % (self.url,))
			self.fetch()
			self.save()
			if self.error is None:
				info("page %s retrieved successfully!" % (self.url,))
	
	def put(self, *a, **k):
		if self.content is None:
			self.fetch()
		super(type(self), self).put(*a,**k)

	@classmethod
	def find_all(cls, owner, limit=50):
		return db.Query(cls).filter('owner =', owner).order('-date').fetch(limit=limit)
	
	@classmethod
	def find(cls, owner, url):
		return db.Query(cls).filter('owner =', owner).filter('url =', url).get()
	
	def as_html(self):
		return render('page.html', {'content':self.content, 'error': self.error is not None})
	html = property(as_html)
	
	#todo: "host" and "soup" attributes (derived)

