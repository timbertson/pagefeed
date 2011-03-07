#!/usr/bin/env python

import os
os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'

import logging
import wsgiref.handlers
from google.appengine.ext import webapp
from pagefeed.controllers.admin import MigrateHandler, ContentCronHandler

application = webapp.WSGIApplication([
		(r'/admin/migrate/(?:([^/]+)/?)?', MigrateHandler),
		(r'/admin/cron/content', ContentCronHandler),
		], debug=True)

def main():
	logging.getLogger().setLevel(logging.DEBUG)
	wsgiref.handlers.CGIHandler().run(application)

if __name__ == '__main__':
	main()
