from os import path
import sys

app_path = path.abspath(path.dirname(path.dirname(__file__)))
if app_path not in sys.path:
	sys.path.insert(0, app_path)

from mocktest import *


