#!/usr/bin/env python2.5
import sys, os
appengine = '/usr/local/google_appengine'
libs = appengine + '/lib/'
sys.path.append(appengine)

for lib in os.listdir(libs):
	sys.path.append(libs + lib)
