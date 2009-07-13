from mocktest import *
from models import page_parser

class PageParserTest(TestCase):
	def assertParses(self, input, expected):
		output = page_parser.parse(input, 'dontcare')
		self.assertEquals(unicode(output), expected)

	def test_should_try_stripping_out_script_tags_on_unparseable(self):
		html = """<html><script></scr + ipt></script><body>caf\xc3\xa9</body>""" # note the utf-8 "acute accented e"
		self.assertParses(html, u'<html><body>caf\xe9</body></html>') # correctly unicode'd

	def test_should_fix_double_quoted_attributes(self):
		html = """<body><link href="style.css"" alt="whatever"></body>"""
		self.assertParses(html, u'<body><link href="style.css" alt="whatever" /></body>')

	def test_should_fix_missing_quotes_on_attributes(self):
		html = """<body><div width="10 height="100">stuff</div></body>"""
		self.assertParses(html, u'<body><div width="10" height="100">stuff</div></body>')

	def test_should_fix_unclosed_tags(self):
		html = """<body><a href="http://foo"<b>click!</b></a></body>"""
		self.assertParses(html, u'<body><a href="http://foo"><b>click!</b></a></body>')

