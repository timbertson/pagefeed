import traceback
import re
from logging import debug, info, warning
from google.appengine.ext import db
from google.appengine.api import users
from google.appengine.ext.db.polymodel import PolyModel

from helpers import view
from base import BaseModel

class ActionProperty(db.StringProperty):
	pass # don't do validation for now

class TransformError(RuntimeError):
	pass

class Transform(PolyModel, BaseModel):
	host_match = db.TextProperty(required=True)
	selector = db.StringProperty()
	owner = db.UserProperty(required=True)
	index = db.IntegerProperty()
	
	def apply(self, soup):
		pass
	
	@classmethod
	def find_all_for_user_and_host(cls, owner, host):
		return db.Query(cls).filter('owner =', owner).filter('host_match =', host).order('index').fetch(limit=50)
	
	@classmethod
	def apply_transform(cls, transform, page):
		debug("applying transform %s to page at url: %s" % (transform, page.url))
		try:
			transform.apply(page)
		except RuntimeError, e:
			errmsg = "transform %s failed: %s" % (type(transform).__name__, e)
			info(errmsg)
			info(traceback.format_exc())
			raise TransformError(errmsg)
	
	@classmethod
	def process(cls, page):
		transforms = cls.find_all_for_user_and_host(page.owner, page.host)
		transforms = cls._monkeypatch_dzone(page, transforms)
		[cls.apply_transform(transform, page) for transform in transforms]
	
	@classmethod
	def _monkeypatch_dzone(cls, page, transforms): #FIXME: !!!
		if transforms: return transforms
		dzone = 'dzone.com'
		if page.host.endswith(dzone) and users.is_current_user_admin():
			debug("monkeypatching dzone transformer...")
			transforms = [FollowTransform(owner=page.owner, host_match=dzone)]
		return transforms
	

def apply_selector(content, sel):
	return BeautifulSoupTraverser.select(content, sel)

class SelectorError(ValueError):
	pass

class BeautifulSoupTraverser(object):
	@staticmethod
	def stripall(lst):
		return map(lambda s: s.strip(), lst)

	@classmethod
	def select(cls, content, selector):
		debug("selector: %r" % (selector,))
		parts = cls.split_parts(selector)
		debug("parts: %r" % (parts,))
		results = []
		for part in parts:
			pipeline = cls.split_pipes(part)
			debug("pipeline: %r" % (pipeline,))
			if not pipeline:
				continue
			part_results = [content]
			for pipe in pipeline:
				debug("applying single selector %r to content %r" % (pipe, part_results))
				part_results = cls.select_over_list(part_results, pipe)
			results += part_results
		return results

	
	@classmethod
	def select_over_list(cls, contents, single_selector):
		results = []
		sel = cls.single_selection_attrs(single_selector)
		has_index = bool(sel['index'])
		if has_index:
			idx = int(sel['index'])
		attr = sel['just_attr'] or sel['attr']
		has_filter = bool(sel['tag'] or sel['attr'] or sel['just_attr'])

		def _index(items):
			if has_index:
				debug("getting index %s of %r (%s)" % (idx, items, len(items)))
				items = [items[idx]]
			return items

		def _filter(items):
			ret = []
			for content in items:
				filtered = []
				args = []
				kwargs = {}
				if sel['tag']:
					args.append(sel['tag'])
				if attr:
					val = True if sel['just_attr'] else sel['value']
					kwargs['attrs'] = {attr:val}
				debug("findall(%r, %r)" % (args, kwargs))
				filtered = content.findAll(*args, **kwargs)
				if has_index:
					filtered = _index(filtered)
				ret.extend(filtered)
			return ret

		if has_filter:
			contents = _filter(contents)
		else:
			contents = _index(contents)
		return contents

	@classmethod
	def split_parts(cls, selector):
		return cls.stripall(selector.split(','))

	@classmethod
	def split_pipes(cls, selector):
		return cls.stripall(selector.split('|'))

	@classmethod
	def single_selection_attrs(cls, selector):
		alpha_match = '[-.a-zA-Z _]+'
		number_match = '-?[0-9]+'
		
		attr_match = '(?P<just_attr>%s)' % (alpha_match,)
		index_match = '(?P<index>%s)' % (number_match,)
		attr_with_value_match = '(?P<attr>%s)=(?P<value>%s)' % (alpha_match, alpha_match)
		inside_bracket_match = '(?:%s|%s|%s)' % (attr_match, attr_with_value_match, index_match)

		match_str = '^(?P<tag>%s)?(?:\[%s\])?$' % (alpha_match, inside_bracket_match,)
		debug("matcher: %r" % (match_str,))
		matcher = re.compile(match_str)
		match = matcher.match(selector)
		if not match:
			raise SelectorError("not a valid selector: %r" % (selector,))

		matches = match.groupdict()
		debug("matched dict for %s is %r" % (selector, matches))

		return matches

class FollowTransform(Transform):
	name = "follow link"
	def apply(self, page):
		# hardcoded for dzone (for now)
		link_details = page.soup.find(attrs={'id':'linkDetails'}).find(attrs={'class':'ldTitle'})
		link = link_details.find('a', attrs={'href':True})
		href = link['href']
		if href.startswith('/'):
			href = "http://%s%s" % (page.host, href)
		info("replacing with contents from: %s" % (href,))
		page.replace_with_contents_from(href)

class DeleteTransform(Transform):
	name = "remove items"
	def apply(self):
		pass
	
class SelectTransform(Transform):
	name = "select subsets of page"
	def apply(self):
		pass
	
