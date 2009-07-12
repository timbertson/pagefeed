import re

from lib.BeautifulSoup import BeautifulSoup, HTMLParseError, UnicodeDammit


class Unparseable(ValueError):
	pass

def parse(raw_content, notify=lambda x: None):
	for parse_method in _parse_methods():
		try:
			return parse_method(raw_content)
		except HTMLParseError, e:
			notify("parsing (%s) failed: %s" % (parse_method.__name__, e))
			continue
	raise Unparseable()

def get_title(soup):
	title = unicode(getattr(soup.title, 'string', ''))
	if not title:
		return None
	return normalize_spaces(title)

def get_body(soup):
	[ elem.extract() for elem in soup.findAll(['script', 'link', 'style']) ]
	return unicode(soup.body or soup)

def ascii(s):
	return s.decode('ascii', 'ignore')

class Replacement(object):
	def __init__(self, desc, regex, replacement):
		self.desc = desc
		self.regex = regex
		self.replacement = replacement
	
	def apply(self, content):
		return self.regex.sub(self.replacement, content)

# a bunch of regexes to hack around lousy html
dodgy_regexes = (
	Replacement('javascript',
		regex=re.compile('<script.*?</script[^>]*>', re.DOTALL | re.IGNORECASE),
		replacement=''),
	Replacement('double double-quoted attributes',
		regex=re.compile('(="[^"]+")"+'),
		replacement='\\1'),
	)

# helpers for parsing
def normalize_spaces(s):
	"""replace any sequence of whitespace
	characters with a single space"""
	return ' '.join(s.split())

def _remove_crufty_html(content):
	for replacement in dodgy_regexes:
		content = replacement.apply(content)
	return content

def _parse_methods():
	def unicode_cleansed(content):
		content = UnicodeDammit(content, isHTML=True).markup
		return BeautifulSoup(_remove_crufty_html(content))

	def ascii_cleansed(content):
		content = ascii(content)
		return BeautifulSoup(_remove_crufty_html(content))

	return (
		BeautifulSoup,
		unicode_cleansed,
		ascii_cleansed)


