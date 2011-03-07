#!/usr/bin/env python2.5
import sys, os
import tempfile

def add_load_path(p):
	if not p in sys.path:
		sys.path.append(p)

appengine = os.environ.get('GAE_HOME') or '/usr/local/google_appengine'
def add_gae_paths():
	libs = appengine + '/lib/'
	paths = [appengine] + [libs + d for d in os.listdir(libs)]
	add_load_path(libs + 'yaml/lib/')
	map(add_load_path, paths)

def init_gae(**opts):
	from google.appengine.dist import use_library
	use_library('django', '0.96')
	from google.appengine.tools import dev_appserver
	from google.appengine.tools.dev_appserver_main import \
		DEFAULT_ARGS, ARG_CLEAR_DATASTORE, \
		ARG_DATASTORE_PATH, ARG_HISTORY_PATH

	# start GAE!
	gae_opts = DEFAULT_ARGS.copy()
	gae_opts[ARG_CLEAR_DATASTORE] = True
	gae_opts[ARG_DATASTORE_PATH] = os.path.join(tempfile.gettempdir(),
		'nosegae.datastore')
	gae_opts[ARG_HISTORY_PATH] = os.path.join(tempfile.gettempdir(),
		'gae.datastore.history')
	gae_opts.update(opts)
	config, _junk = dev_appserver.LoadAppConfig(os.curdir, {})
	dev_appserver.SetupStubs(config.application, **gae_opts)

