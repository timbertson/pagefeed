from pagefeed.test.helpers import *
from models import page

class PageTest(TestCase):
	def test_should_load_well_formed_page(self):
		content = """
			<html>
			<title>the title!</title>
			<body>the body!</body>
			</html>
			"""
		result = mock('result').with_children(status_code=200, content=content)
		url = 'http://localhost/some/path'
		mock_on(page).fetch.is_expected.with_(url).returning(result.raw)
		
		p = page.Page(url=url, owner=a_user)
		p.put()
		self.assertEqual(p.title, 'the title!')
		self.assertEqual(p.content, '<body>the body!</body>')



