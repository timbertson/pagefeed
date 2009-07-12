from google.appengine.ext import db
class BaseModel(db.Model):
	version = db.IntegerProperty(default=0)


