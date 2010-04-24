import urllib2
from models import UserID
from logging import info
from server_errors import HttpError

from google.appengine.api import users

def auth(handle, email):
		email = urllib2.unquote(email)
		if not UserID.auth(email, int(handle)):
			info("invalid credentials: %s-%s" % (email, handle))
			raise HttpError(403, "invalid credentials... ")
		user = users.User(email)
		return user
