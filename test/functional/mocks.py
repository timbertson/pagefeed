import os
from mocktest import *
from webtest import TestApp

from google.appengine.api import users

from pagefeed.main import application
from models.page import Page

user = users.User('foo@example.com')

def app():
	os.environ['USER_EMAIL'] = user.email()
	os.environ['SERVER_NAME'] = 'localhost'
	os.environ['SERVER_PORT'] = '8000'
	return TestApp(application)

app_root = 'http://localhost/'

def stub_page(page=None):
	mock_on(Page).fetch
	if page is None:
		page = Page(url='http://localhost/whatever', title='page title', owner=user)
	page.put()
	page_id = page.key()
	mock_on(Page).find_all.returning([page])
	return page

