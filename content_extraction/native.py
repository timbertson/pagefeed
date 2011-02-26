from pagefeed.lib import page_parser
from ..content import Content

def extract(url):
	content = Content(url)
	logging.info("fetching %r with native extractor" % (url,))
	try:
		soup = page_parser.parse()
		content.body = page_parser.parse()
		content.title = soup.title
	except (page_parser.Unparseable, AttributeError):
		raise(deferred.PermanentTaskFailure())
	logging.info("fetched %r with native extractor, got content size %s" % (url,content.size))
	
