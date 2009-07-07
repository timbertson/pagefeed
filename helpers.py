from os import path
import logging
from google.appengine.ext.webapp import template

CONTENT = 'content'
HEADER = 'header'
LAYOUT = 'layout'

def view(*parts):
	return path.join(path.dirname(__file__), 'views', *parts)

def host_for_url(url):
	try:
		return url.split('/')[2]
	except IndexError:
		logging.error("could not extract host from URL: %r" % (url,))
		return None


def render(*args):
	"""render(dir, [dir, [ ... ]], values)"""
	if len(args) < 2:
		raise ArgumentError("at least 2 args required")
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
	layout_values = dict(
		title = values.get('title', None),
		header = header,
		content = content)
	return render(LAYOUT, layout, layout_values)

