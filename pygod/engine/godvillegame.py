from urllib.parse import quote
from urllib.request import urlopen
from . import godvillenet

class GodvilleGameCom(godvillenet.GodvilleNet):
	ROOT = 'https://godvillegame.com'
	def id(self):
		return 'godvillegame'
	def name(self):
		return 'Godville Game'
	def _quote_godname(self, godname):
		return quote(godname)

	def get_api_url(self, godname, token=None):
		url = self.ROOT + '/gods/api/{0}.json'.format(self._quote_godname(godname))
		return url

	def fetch_state(self, godname, token=None, custom_url=None):
		url = custom_url or self.get_api_url(godname)
		connection = urlopen(url)
		return connection.read().decode('utf-8')
