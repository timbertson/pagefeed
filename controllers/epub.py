from base import *
from lib import epub
from models import Page
from token_auth import auth
import time

class EpubHandler(BaseHandler):
	def get(self, handle, email):
		user = auth(handle, email)
		pages = Page.find_all(user).fetch(limit=50)
		title = "Pagefeed: %s" % (time.strftime("%A %d %B %Y"),)

		book = epub.EPub(title=title, namespace='com.appspot.pagefeed', publisher='gfxmonk')

		for page in pages:
			book.add_section(page.title, page.content)

		self.response.headers['Content-Type'] ='application/zip'
		timestamp = time.strftime("%d-%m-%Y_%H%M%S")
		self.response.headers['Content-Disposition'] = 'attachment; filename="pagefeed_%s.epub"' % (timestamp,)

		book.package()
		self.response.out.write(book.contents())
