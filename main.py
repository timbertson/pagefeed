#!/usr/bin/env python
#
# Copyright 2007 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


import wsgiref.handlers
from google.appengine.ext import webapp
from google.appengine.api import users
from google.appengine.ext.webapp import template

import os
from models import Page

class BaseHandler(webapp.RequestHandler):
	def user(self):
		user = users.get_current_user()
		if user:
			return user
		else:
			self.redirect(users.create_login_url(self.request.uri))
		
	def url(self):
		url = self.request.get_all('url')
		if url:
			return url
		return self.error(400)

class MainHandler(BaseHandler):
	def get(self):
		url = self.request.get('url')
		if url:
			Page(owner=self.user(), url=url).put()
		else:
			user = self.user()
			template_values = {
				'user': user,
				'pages': Page.find_all(user),
				'uri': self.request.uri,
			}
			path = os.path.join(os.path.dirname(__file__), 'index.rss')
			self.response.out.write(template.render(path, template_values))

	def post(self):
		Page(owner=self.user(), url=self.url()).put()

	def delete(self):
		Page.find(owner=self.user(), url=self.url()).delete()
		
def main():
	application = webapp.WSGIApplication([
		('/', MainHandler),
		], debug=True)
	wsgiref.handlers.CGIHandler().run(application)

if __name__ == '__main__':
	main()
