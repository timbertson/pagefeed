import logging
from google.appengine.api.urlfetch import fetch, DownloadError
from django.utils import simplejson as json
import urllib
from google.appengine.ext import deferred
from models import Content

def extract(page):
	url = page.content_url
	content = Content(url=url, source='viewtext')

	viewtext_url = "http://viewtext.org/api/text?url=%(url)s&format=json&rl=false" % {'url': urllib.quote(url)}
	logging.debug("fetching: %s with viewtext extractor" % (viewtext_url,))
	response = fetch(viewtext_url, allow_truncated=False, deadline=20)
	if response.status_code >= 400:
		logging.warning("request returned status code %s\n%s" % (response.status_code, response.content))
		raise DownloadError("request returned status code %s" % (response.status_code,))

	response = json.loads(response.content)
	logging.info("got JSON response with keys: %s" % (response.keys(),))

	try:
		#TODO: remove this hack once viewtext.org adds base href to links.
		# Although, we should prbably still clean content - script tags and such..
		body = response['content']
		from lib import page_parser
		body = page_parser.get_body(page_parser.parse(body))

		content.body = body
		content.title = response['title']
	except KeyError, e:
		raise deferred.PermanentTaskFailure("%s: %s" % (type(e), e))
	content.put()
	logging.info("fetched %r with viewtext extractor, got content size %s" % (url,content.size))
