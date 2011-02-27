from google.appengine.ext import db
from google.appengine.ext import deferred

from google.appengine.api.urlfetch import fetch, DownloadError
from view_helpers import render
from lib.url_helpers import host_for_url
import time
from lib.Python26HTMLParser import HTMLParser

from logging import debug, info, warning, error
from transform import Transform, TransformError
from base import BaseModel
from content import Content
import lib.readability as parser


MESSAGE_TYPES = ['error', 'info']
CONTENT_EXTRACTORS = ['native', 'view_text']

# basic flow of a Page model:
# step 1: add page with URL
#  - does not show in RSS, content is None
#  - does appear in API (android app), but with no content
# step 2: if transforms are defined, perform transforms
#  - this may require fetching the raw HTML
#  - if this fails, an error is logged and applied_transforms is just set to True
# step 3 to 3+n: extract content using all available content extractors
# step 4+n: get best content from steps above, and save it as self.content
#  - now page will appear in RSS, and content will appear in API


def get_content_extractor(name):
	import content_extractors
	return getattr(content_extractors, name)

def task_extract_content(extractor, page_key):
	page = Page.get(page_key)
	if page.content:
		info("skipping content extraction [%s] for page %s, as content is already populated" %
			(extractor, page_key))
		return
	try:
		get_content_extractor(extractor).extract(page)
	except Exception, e:
		error("content extraction %s for page:%s failed with error <%s: %s>" %
			(extractor.__name__, page_key, type(e), e))
		raise
	finally:
		deferred.defer(task_store_best_content, page_key)

def task_store_best_content(page_key, force=False):
	page = Page.get(page_key)
	if page.content:
		return
	contents_found = Content.for_url(page.content_url)
	if force is False and len(contents_found) < len(CONTENT_EXTRACTORS):
		return
	debug("assigning best content for page: %s" % page)
	try:
		best_content = max(contents_found)
	except ValueError:
		error("failed to save content for page %s - no contents were retrieved")
		best_content = Content(url=page.content_url, title=page.default_title(), body="")
	page.content = best_content.body
	page.title = best_content.title
	page.put()
	map(lambda content:content.delete(), contents_found)

class Page(BaseModel):
	url = db.URLProperty(required=True)
	_content_url = db.URLProperty()
	content = db.TextProperty()
	raw_content = db.TextProperty() # TODO: should not be stored on the page itself; it's an intermediate result
	_title = db.StringProperty()
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

	def _get_title(self):
		return self._title or self.default_title()
	def _set_title(self, title):
		self._title = title
	title = property(_get_title, _set_title)

	def get_raw_content(self):
		if self.raw_content is None:
			self._fetch_raw_content()
		return self.raw_content

	def start_content_population(self):
		self.put()
		self.apply_transforms()
		for extractor in CONTENT_EXTRACTORS:
			print "queuing %s" % (extractor,)
			print repr(deferred.defer)
			deferred.defer(task_extract_content, extractor, self.key())
			deferred.defer(task_store_best_content, self.key(), force=True, _countdown = 60 * 10)

	def apply_transforms(self):
		try:
			Transform.process(self)
		except TransformError, e:
			self.error(str(e))

	def _fetch_raw_content(self):
		try:
			response = fetch(self.content_url, allow_truncated=True, deadline=20)
			if response.status_code >= 400:
				warning("request returned status code %s\n%s" % (response.status_code, response.content))
				raise DownloadError("request returned status code %s" % (response.status_code,))
			self.raw_content = response.content
			self.put()
		except DownloadError, e:
			self.error(str(e))
	
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
	
	def json_attrs(self):
		pagetime = int(time.mktime(self.date.timetuple()))
		title = self.title
		try:
			title = HTMLParser().unescape(title)
		except StandardError, e:
			info("couldn't html-decode title: %s" % (e,))
		return {'date':pagetime, 'url':self.url, 'title':title, 'has_content': bool(self.content)}

	@classmethod
	def find_all(cls, owner):
		"returns all objects, inclusing those whose content has not been downloaded"
		return db.Query(cls).filter('owner =', owner).order('-date')

	@classmethod
	def find_complete(cls, owner):
		"returns only pages whose content has been fetched"
		return filter(lambda p:p.content is not None, cls.find_all(owner))
	
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
		self.raw_content = None
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

