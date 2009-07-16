from pagefeed.test.helpers import *
from models import transform
from google.appengine.api import users

from pagefeed.test import fixtures

class TransformAddTest(TestCase):
	path = "/transform/"
	
	def tearDown(self):
		[t.delete() for t in transform.Transform.all()]

	def add(self, **kwargs):
		return fixtures.app().post(self.path + 'add/', kwargs)

	def get(self, **kwargs):
		return fixtures.app().get(self.path)

	def delete(self, key):
		return fixtures.app().post(self.path + 'del/', {'key':key})

	@ignore
	def test_should_add_a_transform_and_redirect_to_index(self):
		sel = 'div[class=foo]'
		kw = dict(owner=fixtures.a_user, host_match='localhost', selector=sel, name="xform")
		xform = mock('transform')
		mock_on(transform.Transform).create.is_expected.with_(**kw).returning(xform)
		response = self.add(**kw)
		self.assertEqual(response.follow().request.url, fixtures.app_root + 'transform/')


	@ignore
	def test_should_delete_a_transform_and_redirect_to_index(self):
		xform = mock('transform')
		key = '1234'
		mock_on(transform.Transform).get.is_expected.with_(key).returning(xform)
		xform.expects('delete')
		
		response = self.delete(key)
		self.assertEqual(response.follow().request.url, fixtures.app_root + 'transform/')

	@ignore
	def test_should_update_an_existing_transform(self):
		#TODO: transform editing
		pass

	@ignore
	def test_should_show_a_list_of_transforms(self):
		response = self.add(owner=fixtures.a_user, host_match='localhost', selector='div[class]', name="transform 1")
		print response.body
		response.mustcontain("transform 1")
		response.mustcontain("div[class]")
		response.mustcontain("localhost")
		self.assertEqual(response.follow().request.url, fixtures.app_root + 'transform/')



