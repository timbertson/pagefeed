from os import path
import sys
from mocktest import *

base_path = path.abspath(path.join(path.dirname(__file__), '..'))
if not base_path in sys.path:
	sys.path.insert(0, base_path)

from pagefeed import console
console.init_gae()

import fixtures
from fixtures import *
from pagefeed.lib.BeautifulSoup import BeautifulSoup

from google.appengine.api import users
from google.appengine.ext import db

class CleanDBTest(TestCase):
	def setUp(self):
		from pagefeed.models import Page, Content
		super(CleanDBTest, self).setUp()
		db.delete(Page.all())
		db.delete(Content.all())

