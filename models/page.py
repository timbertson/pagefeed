from google.appengine.ext import db

from google.appengine.api.urlfetch import fetch, DownloadError
from view_helpers import render, view
from lib.url_helpers import host_for_url

from lib.BeautifulSoup import BeautifulSoup, HTMLParseError, UnicodeDammit
from logging import debug, info, warning, error
from transform import Transform, TransformError
from base import BaseModel
import lib.readability as parser

import re

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

	def default_title(self):
		try:
			return "[%s saved item]" % (parser.ascii(self.host),)
		except StandardError:
			return '[pagefeed saved item]'

	def populate_content(self, raw_content):
		import sys
		try:
			page = parser.Document(raw_content, url=self.base_href, notify=self.info)
			self.title = page.title() or self.default_title()
			self.put(failsafe=True) # ensure the datastore has *something*, even if parsing never completes
			#TODO: get summary working with decent performance
			#self.content = page.summary()
			self.content = page.content()
		except parser.Unparseable, e:
			self._failed("failed to parse content")
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
			response = fetch(self.content_url, allow_truncated=True, deadline=8)
			if response.status_code >= 400:
				warning("request returned status code %s\n%s" % (response.status_code, response.content))
				raise DownloadError("request returned status code %s" % (response.status_code,))
			self.populate_content(response.content)
		except DownloadError, e:
			self._failed(str(e))
	
	def _failed(self, error):
		warning("parse error: %s (url is: %s)" % (error,self.content_url))
		self.title = self.default_title()
		self.content = '' #TODO: make this just a default on the content attribute
		self.error(error)
	
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
		if 'failsafe' in k:
			del k['failsafe']
		else:
			if self.content is None:
				self.fetch()
		super(type(self), self).put(*a,**k)

	@classmethod
	def find_all(cls, owner):
		return db.Query(cls).filter('owner =', owner).order('-date')
	
	@classmethod
	def find_since(cls, owner, date):
		return db.Query(cls).filter('owner =', owner).filter('date >=', date).order('date')
	
	@classmethod
	def find(cls, owner, url):
		return db.Query(cls).filter('owner =', owner).filter('url =', url).get()
	
	def as_html(self):
		return render('snippets/page_content.html', {'page':self, 'error': self.errors})
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

