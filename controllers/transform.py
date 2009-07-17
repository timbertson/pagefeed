import cgi

from base import *
from models import Transform

class TransformHandler(BaseHandler):
	root = "/transform/"
	def get(self):
		transforms = Transform.find_all(self.user())
		self.response.out.write(render_page('transforms', {'transforms':transforms}))

	def transform_params(self):
		excluded_properties = ('version', 'index')
		include = lambda key: not (key in excluded_properties or key.startswith('_'))
		return filter(include, Transform.properties())

	def post(self):
		required_params = self.transform_params()
		transform_params = dict(owner=self.user())
		for param in required_params:
			if param in transform_params: continue
			value = self.request.get(param)
			if not value:
				raise ValueError(param)
			transform_params[param] = value
		self.redirect(self.root)

