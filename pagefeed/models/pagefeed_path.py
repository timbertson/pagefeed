#!/usr/bin/env python2.5
import sys, os

def add_load_path(p):
	if not p in sys.path:
		sys.path.append(p)

add_load_path(os.path.abspath(os.path.dirname(__file__)))
