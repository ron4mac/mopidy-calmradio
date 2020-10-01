import logging
import re

from mopidy import httpclient

import requests

logger = logging.getLogger(__name__)


class CalmRadioClient(object):

	urls = {
		'calm_website': 'https://calmradio.com',
		'calm_categories_api': 'http://api.calmradio.com/categories.json',
		'calm_channels_api': 'http://api.calmradio.com/channels.json',
		'calm_arts_host': 'http://arts.calmradio.com',
		'calm_blurred_arts_host': 'http://calmradio.com/kodi/blurred',
		'calm_auth_api': 'https://api.calmradio.com/get_token?user={0}&pass={1}',
		'calm_sua_api': 'http://api.calmradio.com/check?user={0}&pass={1}',
		'calm_favorites_api': 'http://calmradio.com/player/favorites.php?login={0}&token={1}&action={2}&id={3}'
	}

	session = requests.Session()

	search_results = []

	categories = []
	channels = []


	def __init__(self, proxy_config=None, user_agent=None):
		super(CalmRadioClient, self).__init__()
		self.session = requests.Session()
		if proxy_config != None:
			proxy = httpclient.format_proxy(proxy_config)
			self.session.proxies.update({'http': proxy, 'https': proxy})

		full_user_agent = httpclient.format_user_agent(user_agent)
		self.session.headers.update({'user-agent': full_user_agent})
		self.session.headers.update({'cache-control': 'no-cache'})


	def flush(self):
		self.search_results = []


	def do_get(self, url, url_params=None):
		response = self.session.get(url, params=url_params)
		return response


	def authenticate(self, username, password):
		"""
		Authenticates user
		:return: Token if user is valid, Nonee otherwise
		"""

		response = self.do_get(self.urls['calm_auth_api'].format(username, password))

		if response.status_code != 200:
			logger.error('CalmRadio: Error authenticating. Error: ' + response.text)
			return None
		else:
			json = response.json()
			if 'token' in json:
				self.usertoken = json['token']
				logger.info('CalmRadio: Authentication token: %s', self.usertoken)
				return self.usertoken
			else:
				logger.info('CalmRadio: User not authenticated: %s', username)

		return None


	def get_channel_by_id(self, id):
		#logger.info('CalmRadio: Get channel. ' + id)
		catid, chnid = id.split('c')
		for cat in self.channels:
			if cat['category'] == int(catid):
				for chan in cat['channels']:
					if chan['id'] == int(chnid):
						return chan
		return []


	def get_genre_cats(self, id):
		for genre in self.categories:
			if genre['id'] == int(id):
				return genre['categories']

		return []


	def get_cat_chans(self, id):
		for cat in self.channels:
			if cat['category'] == int(id):
				return cat['channels']

		return []


	def get_categories(self):
		if self.categories:
			return True
		response = self.do_get(self.urls['calm_categories_api'])
		if response.status_code != 200:
			logger.error('CalmRadio: Error getting categories. Error: ' + response.text)
			return False
		else:
			self.categories = response.json()
			return True
		

	def get_channels(self):
		if self.channels:
			return True
		response = self.do_get(self.urls['calm_channels_api'])
		if response.status_code != 200:
			logger.error('CalmRadio: Error getting channels. Error: ' + response.text)
			return False
		else:
			self.channels = response.json()
			return True
		

	def do_search(self, query_string, page_index=1):
		logger.info('CalmRadio: Search query: %s', query_string)
		qstr = query_string.lower()
		if not self.channels:
			self.get_channels()

		if page_index == 1:
			self.search_results = []

		for cat in self.channels:
			catid = cat['category']
			for chan in cat['channels']:
				chan['catid'] = catid
				if qstr in str(chan['title']).lower() or qstr in str(chan['description']).lower():
					self.search_results.append(chan)



