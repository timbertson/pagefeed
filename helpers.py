from os import path
import logging
from urlparse import urlparse

from google.appengine.ext.webapp import template

CONTENT = 'content'
HEADER = 'header'
LAYOUT = 'layout'

def view(*parts):
	return path.join(path.dirname(__file__), 'views', *parts)

def host_for_url(url):
	"""
	> host_for_url('http://base/whatever/fdsh')
	'base'
	"""
	try:
		return url.split('/')[2]
	except IndexError:
		logging.error("could not extract host from URL: %r" % (url,))
		return None

def absolute_url(url, base_href):
	"""
	> absolute_url('foo', 'http://base/whatever/fdsh')
	'http://base/whatever/foo'

	> absolute_url('foo/bar/', 'http://base')
	'http://base/foo/bar/'

	> absolute_url('/foo/bar', 'http://base/whatever/fdskf')
	'http://base/foo/bar'

	> absolute_url('http://localhost/foo', 'http://base/whatever/fdskf')
	'http://localhost/foo'
	"""
	proto = urlparse(url)[0]
	if proto:
		return url
	elif url.startswith('/'):
		return '://'.join(urlparse(base_href)[:2]) + url
	else:
		return base_href + url

def render(*args):
	"""render(dir, [dir, [ ... ]], values)"""
	if len(args) < 2:
		raise TypeError("at least 2 args required")
	template_path = view(*(args[:-1]))
	values = args[-1]
	content = template.render(template_path, values)
	return content

def _render_if_exists(path_, values):
	if path.exists(path_):
		return template.render(path_, values)
	return ''

def render_page(name, values, layout='standard.html', partial=False):
	if partial:
		return render(CONTENT, name + '.html', values)
	header  = _render_if_exists(view(HEADER, name + '.html'), values)
	content = _render_if_exists(view(CONTENT, name + '.html'), values)
	layout_values = values.copy()
	layout_values.update(dict(
		title = values.get('title', None),
		header = header,
		content = content))
	return render(LAYOUT, layout, layout_values)

