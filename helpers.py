import os

def view(name):
	return os.path.join(os.path.dirname(__file__), 'views', name)

