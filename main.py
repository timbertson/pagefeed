#!/usr/bin/env python

import logging
import wsgiref.handlers
from google.appengine.ext import webapp
from google.appengine.api import users
from migrate import MigrateHandler

from controllers import *

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
		(r'/migrate/(?:([^/]+)/?)?', MigrateHandler),
		], debug=True)

def main():
	logging.getLogger().setLevel(logging.DEBUG)
	wsgiref.handlers.CGIHandler().run(application)

if __name__ == '__main__':
	main()

