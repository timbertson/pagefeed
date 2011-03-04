from google.appengine.ext import db
from base import BaseModel

class UserID(BaseModel):
	latest_version = 0
	version = db.IntegerProperty(default=latest_version)
	user = db
	email = db.EmailProperty(required=True)
	handle = db.IntegerProperty(required=True)
	
	@staticmethod
	def _new_handle(email):
		import time
		import random
		random.seed((time.clock() * (1 << 32)) + hash(email))
		return random.getrandbits(60)
	
	@classmethod
	def get(cls, email):
		user = db.Query(cls).filter('email =', email).get()
		if not user:
			handle = cls._new_handle(email)
			user = cls(email=email, handle=handle)
			user.put()
		return user

	@classmethod
	def auth(cls, email, handle):
		user = db.Query(cls).filter('email =', email).filter('handle =', handle).get()
		return user is not None


