from os import path
from google.appengine.ext.webapp import template

CONTENT = 'content'
HEADER = 'header'
LAYOUT = 'layout'

def view(*parts):
	return path.join(os.path.dirname(__file__), 'views', *parts)

def render(*args):
	"""render(dir, [dir, [ ... ]], values)"""
	if len(args) < 2:
		raise ArgumentError("at least 2 args required")
	template_path = view(*(args[:-1])
	values = args[-1]
	content = template.render(template_path, values)
	return content

def _render_if_exists(path, values):
	if path.exists(path):
		return template.render(path, values)
	else return ''

def render_page(name, values, title = None, layout='standard.html', partial=False)
	if partial:
		return render(CONTENT, name + '.html', values)
	header  = _render_if_exists(view(HEADER, name + '.html'), values)
	content = _render_if_exists(view(CONTENT, name + '.html'), values)
	layout_values = dict(
		title = title,
		header = header,
		content = content)
	return render(LAYOUT, layout, layout_values)

