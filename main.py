#!/usr/bin/env python

import logging
import wsgiref.handlers
from google.appengine.ext import webapp
from google.appengine.api import users

from controllers import *

def main():
	logging.getLogger().setLevel(logging.DEBUG)
	application = webapp.WSGIApplication([
		('/', MainHandler),
		('/page/', PageHandler),
		('/page/bookmarklet/', PageBookmarkletHandler),
		('/page/del/', PageDeleteHandler),
		# ('/transform/', TransformHandler),
		(r'/feed/(\d+)-([^/]+)/', FeedHandler),
		], debug=True)
	wsgiref.handlers.CGIHandler().run(application)

if __name__ == '__main__':
	main()
