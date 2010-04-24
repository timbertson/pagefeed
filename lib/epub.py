#!/usr/bin/env python
from StringIO import StringIO
from zipfile import ZipFile
import time
import uuid

class EPub(object):
	STANDARD_FILES = {
		'mimetype': 'mimetype',
		'container': 'META-INF/container.xml',
		'content': 'OEBPS/content.opf',
		'toc': 'OEBPS/toc.ncx'
	}
		
	def __init__(self, title='unknown title', namespace='com.example',
			id=None, publisher="unknown", file=None):

		self.sections = []
		self.id = id or uuid.uuid4()
		self.namespace = namespace
		self.title = title
		self.publisher = publisher
		if file is None:
			file = StringIO()
		self.file = file
	
	def add_section(self, title, content):
		self.sections.append(Section(title, content))
	
	def package(self):
		zipfile = ZipFile(self.file, 'w', compression=False)
		zipfile.debug = 3

		zipfile.writestr(self.STANDARD_FILES['mimetype'], 'application/epub+zip')
		zipfile.writestr(self.STANDARD_FILES['container'],
			"""<?xml version="1.0"?>
			<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">
				<rootfiles>
					<rootfile full-path="%s" media-type="application/oebps-package+xml"/>
				</rootfiles>
			</container>
			""" % (self.STANDARD_FILES['content']))
		self._add_sections(zipfile)
		self._add_content_manifest(zipfile)
		self._add_toc(zipfile)

		zipfile.close()
	
	def contents(self):
			return self.file.getvalue()
			self.file.close()
	
	def _add_sections(self, zipfile):
		self.content = []
		i = 0
		for section in self.sections:
			i += 1
			section.index = i
			zipfile.writestr(section.path, section.content.encode('ascii', 'ignore'))
	
	def _add_content_manifest(self, zipfile):
		content = """<?xml version="1.0"?>
			<package version="2.0" xmlns="http://www.idpf.org/2007/opf"
							 unique-identifier="BookId">
			 <metadata xmlns:dc="http://purl.org/dc/elements/1.1/"
								 xmlns:opf="http://www.idpf.org/2007/opf">"""
		content += "<dc:title>%s</dc:title>" % (self.title,)
		content += """
				 <dc:creator>Various</dc:creator>
				 <dc:language>en-US</dc:language> 
				 <dc:rights>N/A</dc:rights>"""
		content += "<dc:publisher>%s</dc:publisher>" % (self.publisher,)
		content += '<dc:identifier id="bookid">urn:uuid:%s.%s</dc:identifier>' % (self.namespace, self.id,)
		content += """
			 </metadata>
			 <manifest>
				<item id="ncx" href="toc.ncx" media-type="application/x-dtbncx+xml"/>"""

		for section in self.sections:
			content += '<item id="%s" href="%s" media-type="application/xhtml+xml"/>\n' % (
				section.id, section.filename)

		content += """
			 </manifest>
			 <spine toc="ncx">"""

		for section in self.sections:
			content += '<itemref idref="%s"/>\n' % (section.id,)
		content += """
			 </spine>
			</package>"""

		zipfile.writestr(self.STANDARD_FILES['content'], content)
	
	def _add_toc(self, zipfile):
		toc = """<?xml version="1.0" encoding="UTF-8"?>
			<ncx xmlns="http://www.daisy.org/z3986/2005/ncx/" version="2005-1">
				<head>"""
		toc += '<meta name="dtb:uid" content="%s.%s"/>' % (self.namespace, self.id)
		toc += """
					<meta name="dtb:depth" content="1"/>
					<meta name="dtb:totalPageCount" content="0"/>
					<meta name="dtb:maxPageNumber" content="0"/>
				</head>
				<docTitle>"""
		toc += "<text>%s</text>" % (self.title,)
		toc += """
				</docTitle>
				<navMap>"""
		
		for section in self.sections:
			toc += """
					<navPoint id="titlepage" playOrder="%(index)s">
						<navLabel>
							<text>%(title)s</text>
						</navLabel>
						<content src="%(filename)s"/>
					</navPoint>""" % section

		toc += """
				</navMap>
			</ncx>
			"""

		zipfile.writestr(self.STANDARD_FILES['toc'], toc)

class Section(object):
	def __init__(self, title, content):
		self.title = title.encode('utf-8')
		self.content = content
	
	def _path(self):
		return "OEBPS/%s" % (self.filename,)
	path = property(_path)
	
	def _filename(self):
		return "%s.xhtml" % (self.id)
	filename = property(_filename)
	
	def _id(self):
		return "section_%s" % (self.index)
	id = property(_id)
	
	def __getitem__(self, name):
		return getattr(self, name)
	

def main():
	import optparse
	p = optparse.OptionParser()
	p.add_option('-f', '--file', default=None, help="output file")
	p.add_option('-t', '--title', default=None, help="book title")
	opts, args = p.parse_args()
	book = EPub(file=opts.file, title=opts.title)
	for arg in args:
		f = open(arg)
		try:
			book.add_section(arg, f.read().decode('utf-8'))
		finally:
			f.close()
	book.package()
	if opts.file is None:
		print book.contents()

if __name__ == '__main__':
	main()
