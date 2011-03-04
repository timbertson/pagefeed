from os import path
import sys
from mocktest import *

base_path = path.abspath(path.join(path.dirname(__file__), '..'))
if not base_path in sys.path:
	sys.path.insert(0, base_path)

from pagefeed import console
console.gae()

import fixtures
from fixtures import *
from pagefeed.lib.BeautifulSoup import BeautifulSoup

from google.appengine.api import users

