from google.appengine.ext import db

from google.appengine.api.urlfetch import fetch, DownloadError
from helpers import render, view, host_for_url

from lib.BeautifulSoup import BeautifulSoup, HTMLParseError, UnicodeDammit
from logging import debug, info, warning, error
from transform import Transform
from base import BaseModel

DEFAULT_TITLE = '[pagefeed saved item]'

import re

MESSAGE_TYPES = ['error', 'info']

class Unparseable(ValueError):
	pass

def ascii(s):
	return s.decode('ascii', 'ignore')

class Replacement(object):
	def __init__(self, desc, regex, replacement):
		self.desc = desc
		self.regex = regex
		self.replacement = replacement
	
	def apply(self, content):
		return self.regex.sub(self.replacement, content)

def normalize_spaces(s):
	"""replace any sequence of whitespace
	characters with a single space"""
	return ' '.join(s.split())

# a bunch of regexes to hack around lousy html
dodgy_regexes = (
	Replacement('javascript',
		regex=re.compile('<script.*?</script[^>]*>', re.DOTALL | re.IGNORECASE),
		replacement=''),
	Replacement('double double-quoted attributes',
		regex=re.compile('(="[^"]+")"+'),
		replacement='\\1'),
	)

class Page(BaseModel):
	url = db.URLProperty(required=True)
	content = db.TextProperty()
	title = db.StringProperty()
	error = db.TextProperty()
	owner = db.UserProperty(required=True)
	date = db.DateTimeProperty(auto_now_add=True)
	_messages = db.StringListProperty()

	def __init__(self, *a, **k):
		super(type(self), self).__init__(*a, **k)
		self.transformed = False
	
	@staticmethod
	def _get_title(soup):
		title = unicode(getattr(soup.title, 'string', DEFAULT_TITLE))
		return normalize_spaces(title)
	
	@staticmethod
	def _get_body(soup):
		[ elem.extract() for elem in soup.findAll(['script', 'link', 'style']) ]
		return unicode(soup.body or soup)

	@staticmethod
	def _remove_crufty_html(content):
		for replacement in dodgy_regexes:
			content = replacement.apply(content)
		return content
	
	def populate_content(self, raw_content):
		try:
			soup = self._parse_content(raw_content)
			self.content = self._get_body(soup)
			self.title = self._get_title(soup)
		except Unparseable, e:
			safe_content = ascii(raw_content)
			self._failed("failed to parse content", safe_content)
			return
		if self.transformed:
			return
		else:
			self.transformed = True
			self.apply_transforms()

	def apply_transforms(self):
		self.content = unicode(Transform.process(self))
	
	@classmethod
	def _parse_methods(cls):
		def unicode_cleansed(content):
			content = UnicodeDammit(content, isHTML=True).markup
			return BeautifulSoup(cls._remove_crufty_html(content))
		
		def ascii_cleansed(content):
			content = ascii(content)
			return BeautifulSoup(cls._remove_crufty_html(content))
		
		return (
			BeautifulSoup,
			unicode_cleansed,
			ascii_cleansed)
	
	def _parse_content(self, raw_content):
		first_err = None
		for parse_method in self._parse_methods():
			try:
				return parse_method(raw_content)
			except HTMLParseError, e:
				if first_err is None:
					first_err = e
				self.info("parsing (%s) failed: %s" % (parse_method.__name__, e))
				continue
		raise Unparseable()

	def fetch(self):
		try:
			response = fetch(self.url)
			if response.status_code >= 400:
				raise DownloadError("request returned status code %s\n%s" % (response.status_code, response.content))
			self.populate_content(response.content)
		except DownloadError, e:
			self._failed(str(e), 'no content was downloaded')
	
	def _failed(self, error, content):
		debug("error: %s" % (error,))
		self.title = DEFAULT_TITLE
		self.error(error)
		self.content = content
	
	def replace_url(self, new_url):
		orig_url = self.url
		self._reset()
		self.info("original url: %s" % (orig_url,))
		self.url = new_url
		self.put()
	
	def update(self):
		if self.errors:
			info("page %s had an error - redownloading...." % (self.url,))
			self._reset()
			self.put()
			if not self.errors:
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
		return render('page.html', {'page':self, 'error': self.errors})
	html = property(as_html)
	
	def _get_host(self):
		return host_for_url(self.url)
	host = property(_get_host)
	
	def _get_soup(self):
		if self.errors:
			return None
		return BeautifulSoup(self.content)
	soup = property(_get_soup)
	
	def _get_base_href(self):
		base_parts = self.url.split('/')
		if len(base_parts) > 3: # more parts than ("http:", "", "server")
			base_parts = base_parts[:-1] # trim the last component
		base = '/'.join(base_parts) + '/'
		return base
	base_href = property(_get_base_href)
	
	def _add_msg(self, type_, msg):
		assert type_ in MESSAGE_TYPES
		self._messages.append("%s %s" % (type_, msg))
		debug("messages are now: " + "\n".join(self._messages))
	
	def _reset(self):
		self.content = None
		self._messages = []

	def _get_messages(self):
		info(self._messages)
		return [msg.split(' ', 1) for msg in self._messages]
	messages = property(_get_messages)
	
	def message_html(self):
		return render('page_messages.html', {'page': self})
	
	def _get_errors(self):
		return filter(lambda msg: msg[0] == 'error', self.messages)
	errors = property(_get_errors)
		
	def error(self, msg): error(msg); self._add_msg('error', msg)
	def info(self, msg):  info(msg); self._add_msg('info', msg)

