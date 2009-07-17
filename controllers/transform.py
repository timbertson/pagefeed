import cgi

from base import *
from models import Transform

class TransformHandler(BaseHandler):
	def get(self):
		transforms = Transform.find_all(self.user())
		render_page('transforms', {'transforms':transforms})

