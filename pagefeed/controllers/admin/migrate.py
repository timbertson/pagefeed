import logging, cgi
from google.appengine.ext import db, webapp
from google.appengine.api import users

from pagefeed.models import *

models = dict(page=Page)

class MigrateHandler(webapp.RequestHandler):
	def write(self, msg):
		logging.info(msg)
		self.response.out.write(cgi.escape(msg) + "\n")

	def get(self, model=None):
		assert users.is_current_user_admin()
		self.response.out.write("<pre>")
		if model is None:
			self.write("please provide a model")
		else:
			self.write("migrating model \"%s\"" % (model,))
			self.load_and_persist(models[model])
		self.response.out.write("</pre>")
	
	def load_and_persist(self, model_class):
		out_of_date_models = self._old(model_class)
		for model in out_of_date_models:
			assert model.version == model_class.latest_version, "%r != %r" % (model.version, model_class.latest_version)
			db.put(model)
			self.write("migrated item key=%s" % (model.key(),))

	def _old(self, model_class):
		return model_class.all().filter('version <', model_class.latest_version)
	
