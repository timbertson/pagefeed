from google.appengine.ext import db

from google.appengine.api.urlfetch import fetch, DownloadError
from helpers import render, view, host_for_url

from lib.BeautifulSoup import BeautifulSoup, HTMLParseError, UnicodeDammit
from logging import debug, info, warning, error
from transform import Transform, TransformError
from base import BaseModel
import page_parser as parser

import re

DEFAULT_TITLE = '[pagefeed saved item]'

MESSAGE_TYPES = ['error', 'info']

class Page(BaseModel):
	url = db.URLProperty(required=True)
	_content_url = db.URLProperty()
	content = db.TextProperty()
	title = db.StringProperty()
	owner = db.UserProperty(required=True)
	date = db.DateTimeProperty(auto_now_add=True)
	_messages = db.StringListProperty()

	def __init__(self, *a, **k):
		super(type(self), self).__init__(*a, **k)
		self.transformed = False

	def populate_content(self, raw_content):
		try:
			page = parser.parse(raw_content, self.base_href, notify=self.info)
			self.content = parser.get_body(page)
			self.title = parser.get_title(page) or DEFAULT_TITLE
		except parser.Unparseable, e:
			safe_content = parser.ascii(raw_content)
			self._failed("failed to parse content", safe_content)
			return
		if self.transformed:
			return
		else:
			self.transformed = True
			self.apply_transforms()

	def apply_transforms(self):
		try:
			Transform.process(self)
		except TransformError, e:
			self.error(str(e))

	def fetch(self):
		try:
			response = fetch(self.content_url)
			if response.status_code >= 400:
				raise DownloadError("request returned status code %s\n%s" % (response.status_code, response.content))
			self.populate_content(response.content)
		except DownloadError, e:
			self._failed(str(e), 'no content was downloaded')
	
	def _failed(self, error, content):
		warning("parse error: %s (url is: %s)" % (error,self.content_url))
		self.title = DEFAULT_TITLE
		self.error(error)
		self.content = content
	
	def replace_with_contents_from(self, new_url):
		self._reset_content()
		debug("replacing page %s with %s" % (self.url, new_url))
		self.info("replacing contents from URL: %s" % (new_url,))
		self._content_url = new_url
		self.put()
	
	def update(self, force=False):
		if force or self.errors:
			info("page %s: update...." % (self.content_url,))
			self._reset()
			self.put()
	
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
		return host_for_url(self.content_url)
	host = property(_get_host)
	
	def _get_soup(self):
		if self.errors:
			return None
		return BeautifulSoup(self.content)
	soup = property(_get_soup)
	
	def _get_content_url(self):
		url = self._content_url or self.url
		return url.split("#", 1)[0]
	content_url = property(_get_content_url)
	
	def _get_base_href(self):
		base_parts = self.content_url.split('/')
		if len(base_parts) > 3: # more parts than ("http:", "", "server")
			base_parts = base_parts[:-1] # trim the last component
		base = '/'.join(base_parts) + '/'
		return base
	base_href = property(_get_base_href)
	
	def _add_msg(self, type_, msg):
		assert type_ in MESSAGE_TYPES
		self._messages.append("%s %s" % (type_, msg))
	
	def _reset_content(self):
		self.content = None
		self._content_url = None
		self._messages = []
	
	def _reset(self):
		self._reset_content()
		self.transformed = False

	def _get_messages(self):
		return [msg.split(' ', 1) for msg in self._messages]
	messages = property(_get_messages)
	
	def message_html(self):
		return render('page_messages.html', {'page': self})
	
	def _get_errors(self):
		return filter(lambda msg: msg[0] == 'error', self.messages)
	errors = property(_get_errors)
		
	def error(self, msg): error(msg); self._add_msg('error', msg)
	def info(self, msg):  info(msg); self._add_msg('info', msg)

