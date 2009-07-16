import re
from logging import debug, info, warning

class SelectorError(ValueError):
	pass

def apply_selector(content, sel):
	return BeautifulSoupTraverser.select(content, sel)

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

