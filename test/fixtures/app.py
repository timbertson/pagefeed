import os
from webtest import TestApp

from pagefeed.main import application

from user import a_user

app_root = 'http://localhost/'

def app():
	os.environ['USER_EMAIL'] = a_user.email()
	os.environ['SERVER_NAME'] = 'localhost'
	os.environ['SERVER_PORT'] = '8000'
	return TestApp(application)


