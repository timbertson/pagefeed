import os
from mocktest import *
from webtest import TestApp

from google.appengine.api import users

from pagefeed.main import application
from models.page import Page

user = 'foo@example.com'

def app():
	os.environ['USER_EMAIL'] = user
	os.environ['SERVER_NAME'] = 'localhost'
	os.environ['SERVER_PORT'] = '8000'
	return TestApp(application)

def stub_page(page=None):
	mock_on(Page).fetch
	if page is None:
		page = Page(url='http://localhost/whatever', title='page title', owner=users.User('foo'))
	page.put()
	page_id = page.key()
	mock_on(Page).find_all.returning([page])
	return page

