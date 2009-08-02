import page_parser
import urllib2

outputs = []

def prnt(s):
	outputs.append(s)
	# print s

def parse(url):
	global outputs
	outputs = []
	raw_content = urllib2.urlopen(url).read()
	page_parser.debug = prnt
	prnt("INITIAL CONTENT: %s" % (raw_content,))
	return page_parser.parse(raw_content, 'http://localhost/')
