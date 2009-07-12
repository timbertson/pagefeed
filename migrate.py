import logging, cgi
from google.appengine.ext import db, webapp
from google.appengine.api import users

from models import *

class MigrateHandler(webapp.RequestHandler):
	def write(self, msg):
		logging.info(msg)
		self.response.out.write(cgi.escape(msg) + "\n")

	def get(self, model=None):
		assert users.is_current_user_admin()
		self.response.out.write("<pre>")
		if model is None:
			migrations = []
			for migration_set in self.migrations_for.values():
				migrations.extend(migration_set)
		else:
			self.write("migrating model \"%s\"" % (model,))
			migrations = self.migrations_for[model]
		self._apply_migrations(migrations)
		
	def _apply_migrations(self, migrations):
		self.current_version = 0
		for migration in migrations:
			self.current_version += 1
			self.write("migrating to version %s: %s" % (self.current_version, migration.__name__))
			migration(self)
		self.response.out.write("</pre>")

	def add_version_number(self, model_class):
		for model in model_class.all():
			if model.version is None or model.version == 0:
				self._update(model)

	def _old(self, model_class):
		return model_class.all().filter('version <', self.current_version)
	
	def _update(self, model):
		self.write("setting version of %r = %s" % (model, self.current_version))
		model.version = self.current_version
		model.put()

	# ----
	
	def page_remove_error(self):
		for page in self._old(Page):
			page.error = None
			self._update(page)
	
	
	# ----
	
	migrations_for = {
	 	'page': [
			lambda self: self.add_version_number(Page),
			page_remove_error,
		],
	}

