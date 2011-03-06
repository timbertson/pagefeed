from pagefeed.controllers.admin import migrate
from google.appengine.ext import db
from StringIO import StringIO
import operator
from test_helpers import *

class TestMigrationModel(db.Model):
	latest_version = 2
	version = db.IntegerProperty(default=latest_version)
	desc = db.StringProperty()
	migrated = db.BooleanProperty(default=False)
	def __init__(self, *a, **k):
		if k.get('version', self.latest_version) < self.latest_version:
			print "upgrading!"
			k['migrated'] = True
			k['version'] = self.latest_version
		super(TestMigrationModel, self).__init__(*a, **k)

	def __repr__(self):
		return repr(self.to_xml())

class TestMigrateHandler(TestCase):
	def handler(self):
		handler = migrate.MigrateHandler()
		handler.response = mock('response')
		handler.response.out = StringIO()
		return handler

	def test_should_load_and_save_all_models_of_an_old_version(self):
		handler = self.handler()
		when(migrate.users).is_current_user_admin().then_return(True)
		modify(migrate).models = {'test':TestMigrationModel}

		old_models = [TestMigrationModel(desc='old1'), TestMigrationModel(desc='old2')]
		old_models[0].version = 0
		old_models[1].version = 1
		current_model = TestMigrationModel(desc='new1', version=2)
		db.put(old_models + [current_model])

		old_models = [TestMigrationModel.get(model.key()) for model in old_models]
		current_model = TestMigrationModel.get(current_model.key())
		
		get_key = lambda x: x.key()

		expect(db).put.where(lambda obj: obj.key() in map(get_key, old_models)).twice()
		expect(db).put.where(lambda obj: obj.key() == current_model.key()).never()

		handler.get(model='test')
	
	def test_should_disallow_access_to_non_admin_users(self):
		handler = self.handler()
		when(migrate.users).is_current_user_admin().then_return(False)
		self.assertRaises(AssertionError, lambda: handler.get(model='test'))
		self.assertEqual(handler.response.out.getvalue(), "")
