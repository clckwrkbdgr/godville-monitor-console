import os, sys, platform
import time, datetime
import urllib.request
import urllib.parse
import http.cookies
import itertools
import json
import random, string
import logging
from collections import Counter

class API:
	""" Very basic The Tale API wrapper (mostly for GET requests).

	Based on: https://docs.the-tale.org/ru/stable/external_api/index.html

	Stores session cookies at $XDG_CACHE_HOME/pygod.cookie.json
	"""
	class Error(RuntimeError): pass
	class AuthRequested(Exception):
		def __init__(self, auth_page): self.auth_page = auth_page
		def __str__(self): return str(self.auth_page)

	VERSION = (0, 1)
	APP_NAME = 'PyGod'
	BASE_URL = 'https://the-tale.org'
	REQUEST_DELAY = 1.0 # seconds

	def __init__(self):
		self.cookiefile = os.path.join(
				os.environ.get('XDG_CACHE_HOME', os.path.expanduser('~/.cache')),
				'pygod.cookie.json',
				)
		if os.path.exists(self.cookiefile):
			with open(self.cookiefile) as f:
				self.cookies = json.loads(f.read())
		else:
			self.cookies = {
				'sessionid': None,
				'csrftoken' : ''.join(random.choice(string.ascii_lowercase + string.digits) for _ in range(32)),
				}
		self.client_id = '{0}-{1}'.format(self.APP_NAME, '.'.join(map(str, self.VERSION)))

		self.account_id = None
		self.last_turn = None
		self.hero_info = {}
		self.account_info = {}
		self.card_info = {}

		self.old_state = None
	def _dump_cookies(self):
		try:
			with open(self.cookiefile, 'w') as f:
				f.write(json.dumps(self.cookies))
		except:
			logging.exception('Failed to dump cookies to {0}'.format(self.cookiefile))
	def _run_request(self, path, method='GET', api_version=None, post_params=None, **query_params):
		method = method.upper()
		api_version = api_version or '1.0'

		headers = {
				'X-CSRFToken' : self.cookies['csrftoken'],
				'Referer': 'https://the-tale.org/',
				'Cookie': '; '.join('='.join((k, v)) for k,v in self.cookies.items() if v is not None),
				}
		query_params = urllib.parse.urlencode({
					'api_version': api_version,
					'api_client': self.client_id,
					})
		if method == 'POST' and post_params:
			post_params = urllib.parse.urlencode(list(post_params.items())).encode('ascii')
		request = urllib.request.Request(self.BASE_URL + path + '?' + query_params,
				data=post_params,
				headers=headers,
				method=method,
				)
		logging.debug('Full URL: {0}'.format(request.get_full_url()))
		logging.debug('Request headers: {0}'.format(request.header_items()))

		request = urllib.request.urlopen(request, timeout=5)
		logging.debug('Response headers: {0}'.format(request.getheaders()))
		new_cookies = {}
		for name, cookie in request.getheaders():
			if name != 'Set-Cookie':
				continue
			cookie = http.cookies.SimpleCookie(cookie)
			for name, c in cookie.items():
				if name == 'SameSite':
					continue
				new_cookies[c.key] = c.value
		logging.debug('New cookies: {0}'.format(new_cookies))
		self.cookies.update(new_cookies)
		logging.debug('Updated cookies: {0}'.format(self.cookies))
		self._dump_cookies()
		response = json.loads(request.read())
		logging.debug('Full response: {0}'.format(response))
		if response.get('deprecated', False):
			logging.warning('Deprecated version: {0}?api_version={1}'.format(path, api_version))
		if response.get('status', 'ok') == 'error':
			raise self.Error('{0}: {1}'.format(response.get('code'), response.get('error', str(response.get('errors')))))
		# TODO if status == 'processing'
		return response['data']
	def authorize(self, force=False):
		AUTH_WAS_NOT_REQUESTED = 0
		AUTH_NOT_CONFIRMED_BY_USER = 1
		AUTH_SUCCESS = 2
		AUTH_REFUSED = 3
		auth_state = self._run_request('/accounts/third-party/tokens/api/authorisation-state', api_version='1.0')
		self.account_id = auth_state['account_id']
		if auth_state['state'] == AUTH_NOT_CONFIRMED_BY_USER:
			logging.debug('Authorization: Not confirmed by user.')
			if force:
				logging.debug('Authorization:   Forcing: considering as not requested.')
				auth_state['state'] = AUTH_WAS_NOT_REQUESTED
			else:
				logging.debug('Authorization:  Is not confirmed by user yet.')
				raise self.AuthRequested(None)
		if auth_state['state'] == AUTH_REFUSED:
			logging.debug('Authorization: Refused!')
			raise self.Error('Authorisation refused by server.')
		if auth_state['state'] == AUTH_WAS_NOT_REQUESTED:
			time.sleep(self.REQUEST_DELAY)
			auth_request = self._run_request('/accounts/third-party/tokens/api/request-authorisation', api_version='1.0', method='POST',
					post_params={
						'application_name' : self.APP_NAME,
						'application_info' : 'Device: ' + ' '.join(platform.uname()),
						'application_description' : 'Console monitor for The Tale: https://github.com/clckwrkbdgr/godville-monitor-console',
						},
					)
			logging.debug('Authorization: Raising request for authorization.')
			if not self.old_state:
				# Dummy state so next time auth is requested, it is not foced
				# and sticks with just received token.
				self.old_state = {
					'token_expired' : True,
					}
			raise self.AuthRequested(self.BASE_URL + auth_request['authorisation_page'])
		logging.debug('Authorization: OK.')
	def get_hero_state(self):
		logging.debug('Old state present: {0}'.format(bool(self.old_state)))
		if not self.account_id:
			logging.debug('Account ID is not set, performing authorization (force={0})...'.format(not bool(self.old_state)))
			self.authorize(force=not bool(self.old_state))
		now = time.time()
		current_min = time.localtime(now).tm_min
		if 59 <= current_min or current_min <= 2:
			# Game server performs hourly cron job to update game world
			# at the first couple of minutes each hour.
			# It's better to skip updates within this time interval if possible.
			# <https://the-tale.org/forum/threads/939?page=34#m269753>
			if self.old_state:
				return self.old_state

		ACCOUNT_INFO_REFRESH_RATE = 30 * 60 # sec
		CARD_INFO_REFRESH_RATE = 10 * 60 # sec
		ACTION_IN_TOWN = 5

		if not self.last_turn:
			logging.debug('Last turn was not found, performing full refresh...')
			game_info = self._run_request('/game/api/info', account=self.account_id,
					api_version='1.10')
		else:
			logging.debug('Performing refresh since last turn ({0})...'.format(self.last_turn))
			game_info = self._run_request('/game/api/info', account=self.account_id,
					client_turns=self.last_turn,
					api_version='1.10')
		account = game_info['account']
		if not account or not account['hero']:
			logging.debug('Game account info is not present, performing authorization (force={0})...'.format(not bool(self.old_state)))
			self.authorize(force=not bool(self.old_state))
			return self.old_state
		self.hero_info.update(account['hero'])
		self.last_turn = game_info['turn']['number']

		if not self.account_info or self.account_info['_last_update'] + ACCOUNT_INFO_REFRESH_RATE < now:
			logging.debug('Refreshing account info...')
			time.sleep(self.REQUEST_DELAY)
			self.account_info = self._run_request('/accounts/{0}/api/show'.format(self.account_id),
					api_version='1.0')
			self.account_info['_last_update'] = now

		if not self.card_info or self.card_info['_last_update'] + CARD_INFO_REFRESH_RATE < now:
			logging.debug('Refreshing card info...')
			time.sleep(self.REQUEST_DELAY)
			self.card_info = self._run_request('/game/cards/api/get-cards',
					api_version='2.0')
			self.card_info['_last_update'] = now

		state = {
				"_hero_info" : self.hero_info,
				"_account_info" : self.account_info,
				"_card_info" : self.card_info,
			"name": self.hero_info['base']['name'],
			"godname": self.account_info['name'],
			"gender": ["male", "female"][self.hero_info['base']['gender']],
			"level": self.hero_info['base']['level'],
			"max_health": self.hero_info['base']['max_health'],
			"inventory_max_num": self.hero_info['secondary']['max_bag_size'],
			"motto": "", # TODO Meaningless in The Tale.
			"clan": (self.account_info['clan'] or {}).get('name'),
			"clan_position": "", # TODO Cannot be directly fetched in The Tale.
			"alignment": ' '.join((
				self.hero_info["habits"]["honor"]["verbose"],
				self.hero_info["habits"]["peacefulness"]["verbose"],
				)),
			"bricks_cnt": 0, # TODO Meaningless in The Tale.
			"wood_cnt": 0, # TODO Meaningless in The Tale.
			"temple_completed_at": None, # TODO Meaningless in The Tale.
			"pet": {
				"pet_name": "",
				"pet_class": self.hero_info['companion']['name'],
				"pet_level": self.hero_info['companion']['experience'],
			} if self.hero_info['companion'] else {},
			"ark_completed_at": None, # TODO Meaningless in The Tale.
			"savings_completed_at": None, # TODO Meaningless in The Tale.
			"ark_f": 0, # TODO Meaningless in The Tale.
			"ark_m": 0, # TODO Meaningless in The Tale.
			"arena_won": 0, # TODO Meaningless in The Tale.
			"arena_lost": 0, # TODO Meaningless in The Tale.
			"savings": "0", # TODO Meaningless in The Tale.
			"t_level": None, # TODO Meaningless in The Tale.
			"shop_name": None, # TODO Meaningless in The Tale.
			"boss_name": None, # TODO Meaningless in The Tale.
			"boss_power": None, # TODO Meaningless in The Tale.
			"book_at": None, # TODO Meaningless in The Tale.
			"souls_percent": None, # TODO Meaningless in The Tale.
			"health": self.hero_info['base']['health'],
			"quest_progress": int(100/len(list(itertools.chain.from_iterable(
				quest["line"]
				for quest
				in self.hero_info["quests"]["quests"]
				if quest["line"][0]["type"] != "no-quest"
				)))),
			"exp_progress": int(100 * self.hero_info['base']['experience'] / self.hero_info['base']['experience_to_level']),
			"godpower": 0, # TODO Meaningless in The Tale.
			"gold_approx": str(self.hero_info['base']['money']),
			"diary_last": (self.hero_info['messages'] or [(None, None, "...")])[-1][2],
			"town_name": str((self.hero_info["action"]["data"], self.hero_info["action"]["description"])) if self.hero_info["action"]["type"] == ACTION_IN_TOWN else None,
			"distance": 0, # TODO Meaningless in The Tale. Have cartesian coords instead.
			"arena_fight": game_info["mode"] == 'pvp',
			"fight_type": None, # TODO Meaningless in The Tale.
			"inventory_num": len(self.hero_info['bag']),
			"quest": sorted([
				quest["line"][-1]
				for quest
				in self.hero_info["quests"]["quests"]
				if quest["line"][0]["type"] != "no-quest"
				], key=lambda quest: 1 if quest["type"] == 'next-spending' else 0,
				)[0]["name"],
			"activatables": [
					('{0} (x{1})' if amount > 1 else '{0}').format(name, amount)
					for name, amount
					in Counter([
						card["name"]
						for card
						in self.card_info["cards"]
						if not card["in_storage"]
						]).items()
					],
		}

		if not self.hero_info['messages']:
			logging.debug('No history messages. Considering expired.')
			state['expired'] = True
		self.old_state = state
		return state

class TheTale:
	ROOT = 'https://the-tale.org'
	def __init__(self):
		self.api = API()
		self.token_generation_url = None
	def id(self):
		return 'thetale'
	def name(self):
		return 'The Tale'

	def get_hero_url(self):
		return self.ROOT + '/game/'
	def get_token_generation_url(self):
		return self.token_generation_url

	def fetch_state(self, godname, token=None, custom_url=None):
		# TODO Does not need godname actually,
		# because API's session is automatically tied to the account
		# once user is confirmed authorization for the informer app.
		try:
			state = self.api.get_hero_state()
		except API.AuthRequested as e:
			self.token_generation_url = e.auth_page or self.token_generation_url
			logging.warning('Token expired. Authorization requested: {0}'.format(self.token_generation_url))
			state = {
					'token_expired' : True,
					}
		return json.dumps(state)
