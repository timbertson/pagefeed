from lib import page_parser
from pagefeed.models import Content
import logging
from google.appengine.ext import deferred

def extract(page):
	url = page.content_url
	content = Content(url, source='native')
	logging.info("fetching %r with native extractor" % (url,))
	try:
		content = page.get_raw_content()
		soup = page_parser.parse(content, base_href=page.base_href, notify=logging.info)
		content.body = page_parser.get_body(soup)
		content.title = page_parser.get_title(soup)
	except (page_parser.Unparseable, AttributeError), e:
		raise deferred.PermanentTaskFailure("%s: %s" % (type(e), e))
	content.put()
	logging.info("fetched %r with native extractor, got content size %s" % (url,content.size))
	
