import lib.readability as parser
from pagefeed.models import Content
import logging
from google.appengine.ext import deferred

def extract(page):
	url = page.content_url
	content = Content(url, source='native')
	logging.info("fetching %r with native extractor" % (url,))
	try:
		content = page.get_raw_content()
		doc = parser.Document(content, page.base_href, notify=logging.info)
		content.body = doc.content()
		content.title = doc.title()
	except (parser.Unparseable, AttributeError), e:
		raise deferred.PermanentTaskFailure("%s: %s" % (type(e), e))
	content.put()
	logging.info("fetched %r with native extractor, got content size %s" % (url,content.size))
	
