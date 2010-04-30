# usage: ebook-convert pagefeed.recipe <output-file>

import time
from calibre.web.feeds.news import BasicNewsRecipe

class PageFeed(BasicNewsRecipe):
	title = "Pagefeed: %s" % (time.strftime("%A %d %B %Y"),)
	description = "personalized Pagefeed recipe"
	__author__ = 'gfxmonk'
	oldest_article = 30.0
	simultaneous_downloads = 3
	feeds = ['{{feed_url}}']
	cover_url = '{{server_base}}/public/pagefeed-160.png'
	use_embedded_content = True

