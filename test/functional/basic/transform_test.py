from pagefeed.test.helpers import *
from models import transform
from google.appengine.api import users

from pagefeed.test import fixtures


class TransformAddTest(TestCase):
	path = "/transform/"
	default_opts = dict(owner=fixtures.a_user, host_match='localhost', selector='div[class=foo]', name="xform")
	
	def tearDown(self):
		[t.delete() for t in transform.Transform.all()]

	def fill_in_form(self, form, d):
		for k, v in d.items():
			form.set(k, v)

	def add(self, form=None, **kwargs):
		if form is None:
			form = self.get().forms['new_transform']
		fill_in_form(form, kwargs)
		self.assertEqual(form.method, 'POST')
		self.assertEqual(form.action, self.path)
		return form.submit()

	def get(self, **kwargs):
		return fixtures.app().get(self.path)

	def delete(self, form):
		fill_in_form(form, kwargs)
		self.assertEqual(form.method, 'POST')
		self.assertEqual(form.action, self.path + 'del/')
		return form.submit()

	@ignore
	def test_should_add_a_transform_and_redirect_to_index(self):
		kw = dict(owner=fixtures.a_user, host_match='localhost', selector='div[class=foo]', name="xform")
		xform = mock('transform')
		mock_on(transform.Transform).create.is_expected.with_(**kw).returning(xform)
		response = self.add(**kw)
		self.assertEqual(response.follow().request.url, fixtures.app_root + 'transform/')

	@ignore
	def test_should_show_error_message_on_failure(self):
		form = self.get().forms['new_transform']
		response = form.submit(status=400)
		response.mustcontain("Error:")

	@ignore
	def test_should_delete_a_transform_and_redirect_to_index(self):
		delete_form = self.add(**self.default_opts).follow().forms[1] # 0 is add, all others are delete
		def num_transforms():
			return len(transform.Transform.all().fetch(100))
		self.assertEqual(num_transforms(), 1)

		response = self.delete(delete_form)
		self.assertEqual(num_transforms(), 0)
		self.assertEqual(response.follow().request.url, fixtures.app_root + 'transform/')

	@ignore
	def test_should_update_an_existing_transform(self):
		edit_form = self.add(**self.default_opts).follow().forms[2] # 0 is add, all others are (delete, edit) pairs
		for k,v in self.default_opts:
			self.assertEqual(edit_form[k].value, v) #TODO: check webtest API
		def transforms():
			return transform.Transform.all().fetch(5)
		all_xforms = transforms()
		self.assertEqual(len(all_xforms), 1)

		response = self.add(edit_form, name="the second name")
		updated_xforms = transforms()
		self.assertEqual(len(updated_xforms), 1)

		# selector, etc should stay the same:
		self.assertEqual(all_xforms[0].selector, updated_xforms[0].selector)

		# but names should be different:
		self.assertEqual(all_xforms[0].name, self.default_opts['name'])
		self.assertEqual(updated_xforms[0].name, self.default_opts['the second name'])
		
		self.assertEqual(response.follow().request.url, fixtures.app_root + 'transform/')


	@ignore
	def test_should_show_a_list_of_transforms(self):
		response = self.add(owner=fixtures.a_user, host_match='localhost', selector='div[class]', name="transform 1")
		print response.body
		response.mustcontain("transform 1")
		response.mustcontain("div[class]")
		response.mustcontain("localhost")
		self.assertEqual(response.follow().request.url, fixtures.app_root + 'transform/')



