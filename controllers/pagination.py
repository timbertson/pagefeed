from base import *

class PaginatedHandler(BaseHandler):
	items_per_page = 10

	def page(self):
		page = int(self.request.get('page') or 0)
		return page
	
	def paginated(self, query):
		offset = self.page() * self.items_per_page
		return query.fetch(limit=self.items_per_page, offset=offset)
	
	def total_pages(self):
		max_models = ((self.page() + 1) * self.items_per_page) + 1
		model_count = self.all_instances().count(limit=max_models)
		return int(float(model_count) / float(self.items_per_page) + 1)
	
	def page_link(self, num):
		if num < 0 or num >= self.total_pages():
			return None
		return "%s?page=%s" % (self.uri(), num)
	
	def pagination_links(self):
		pagenum = self.page()
		return {
			'next': self.page_link(pagenum + 1),
			'prev': self.page_link(pagenum - 1),
		}

