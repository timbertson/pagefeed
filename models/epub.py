import urllib2

from user import UserID

class Epub(object):

	@staticmethod
	def path_for(user):
		email = user.email()
		user_handle = UserID.get(email).handle
		return '/epub/%s-%s/' % (user_handle, urllib2.quote(email))

