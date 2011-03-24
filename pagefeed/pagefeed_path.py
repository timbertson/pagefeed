#!/usr/bin/env python2.5
import sys, os

def add_load_path(p):
	if not p in sys.path:
		sys.path.append(p)

add_load_path(os.path.abspath(os.path.dirname(__file__)))

from google.appengine.dist import use_library
use_library('django', '0.96')
import warnings
warnings.filterwarnings("ignore", category=UnicodeWarning, module='BeautifulSoup')
