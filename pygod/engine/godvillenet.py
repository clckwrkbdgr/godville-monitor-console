from urllib.parse import quote_plus
from urllib.request import urlopen
import logging

class GodvilleNet:
	ROOT = 'https://godville.net'
	def id(self):
		return 'godvillenet'
	def name(self):
		return 'Godville'
	def _quote_godname(self, godname):
		return quote_plus(godname)

	def get_hero_url(self):
		return self.ROOT + '/superhero'
	def get_api_url(self, godname, token=None):
		url = self.ROOT + '/gods/api/{0}'.format(self._quote_godname(godname))
		if token:
			url += '/{0}'.format(token)
		return url
	def get_token_generation_url(self):
		return self.ROOT + '/user/profile'

	def fetch_state(self, godname, token=None):
		url = self.get_api_url(godname, token)
		connection = urlopen(url, timeout=5)
		if connection is None or connection.getcode() == 404:
			old_url = self.ROOT + '/gods/api/{0}.json'.format(self._quote_godname(godname))
			logging.error(
					'load_hero_state: new api url %s returned 404\n'
					'                 will try old api url %s',
					url, old_url)
			connection = urlopen(old_url, timeout=5)
		return connection.read().decode('utf-8')
