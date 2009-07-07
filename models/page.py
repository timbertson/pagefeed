from google.appengine.ext import db

from google.appengine.api.urlfetch import fetch, DownloadError
from helpers import render, view, host_for_url

from lib.BeautifulSoup import BeautifulSoup, HTMLParseError, UnicodeDammit
from logging import debug, info, warning, error

DEFAULT_TITLE = '[pagefeed saved item]'

import re

class Unparseable(ValueError):
	pass

def ascii(s):
	return s.decode('ascii', 'ignore')

class Page(db.Model):
	url = db.URLProperty(required=True)
	content = db.TextProperty()
	title = db.StringProperty()
	error = db.TextProperty()
	owner = db.UserProperty(required=True)
	date = db.DateTimeProperty(auto_now_add=True)
	
	@staticmethod
	def _get_title(soup):
		return unicode(getattr(soup.title, 'string', DEFAULT_TITLE))
	
	@staticmethod
	def _get_body(soup):
		[ elem.extract() for elem in soup.findAll(['script', 'link', 'style']) ]
		return unicode(soup.body or soup)

	@staticmethod
	def _remove_script_tags(content):
		script_re = re.compile(
			'<script.*?</script[^>]*>',
			re.DOTALL | re.IGNORECASE)
		print repr(content)
		return script_re.sub('', content)
	
	def _populate_content(self, raw_content):
		self.error = None
		try:
			soup = self._parse_content(raw_content)
			self.content = self._get_body(soup)
			self.title = self._get_title(soup)
		except Unparseable, e:
			safe_content = ascii(raw_content)
			self._failed(str(e), safe_content)
	
	@classmethod
	def _parse_methods(cls):
		def unicode_removed_script_tags(content):
			content = UnicodeDammit(content, isHTML=True).markup
			return BeautifulSoup(cls._remove_script_tags(content))
		
		def ascii_removed_script_tags(content):
			content = ascii(content)
			return BeautifulSoup(cls._remove_script_tags(content))
		
		return (
			BeautifulSoup,
			unicode_removed_script_tags,
			ascii_removed_script_tags)
	
	@classmethod
	def _parse_content(cls, raw_content):
		first_err = None
		for parse_method in cls._parse_methods():
			try:
				return parse_method(raw_content)
			except HTMLParseError, e:
				if first_err is None:
					first_err = e
				error("parsing (with %s) failed: %s" % (parse_method, e))
				continue
		raise Unparseable(str(first_err))

	def fetch(self):
		try:
			response = fetch(self.url)
			if response.status_code >= 400:
				raise DownloadError("request returned status code %s\n%s" % (response.status_code, response.content))
			self._populate_content(response.content)
		except DownloadError, e:
			self._failed(str(e), 'no content was downloaded')
	
	def _failed(self, error, content):
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
	
	def _get_host(self):
		return host_for_url(self.url)
	host = property(_get_host)
	
	def _get_soup(self):
		if self.error:
			return None
		return BeautifulSoup(self.content)
	soup = property(_get_soup)


