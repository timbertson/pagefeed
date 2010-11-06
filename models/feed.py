import urllib2

from user import UserID

class Feed(object):

	@staticmethod
	def path_for(user):
		email = user.email()
		user_handle = UserID.get(email).handle
		return '/feed/%s-%s/' % (user_handle, urllib2.quote(email))
	
	@classmethod
	def url_for(cls, user, host):
		return "https://%s%s" % (host, cls.path_for(user),)

