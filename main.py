#!/usr/bin/env python

import os
os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'

from pagefeed import pagefeed_path
from pagefeed.controllers import *

import logging
import wsgiref.handlers
from google.appengine.ext import webapp
from google.appengine.api import users

application = webapp.WSGIApplication([
		('/', MainHandler),
		('/page/', PageHandler),
		('/logout/', LogoutHandler),
		('/recipe/', RecipeHandler),
		('/page/bookmarklet/', PageBookmarkletHandler),
		('/page/del/', PageDeleteHandler),
		('/page/list/', PageListHandler),
		('/page/update/', PageUpdateHandler),
		('/transform/', TransformHandler),
		('/about/?', AboutHandler),
		('/faq/?', FaqHandler),
		('/transform/del/', TransformDeleteHandler),
		(r'/feed/(\d+)-([^/]+)/', FeedHandler),
		], debug=True)

def main():
	logging.getLogger().setLevel(logging.DEBUG)
	wsgiref.handlers.CGIHandler().run(application)

if __name__ == '__main__':
	main()

