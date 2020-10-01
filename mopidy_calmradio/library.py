import logging
import re

from mopidy import backend
from mopidy.models import Image, Ref, SearchResult, Track

logger = logging.getLogger(__name__)

class CalmRadioLibraryProvider(backend.LibraryProvider):
	root_directory = Ref.directory(uri='calmradio:root', name='Calm Radio')

	def lookup(self, uri):

		if not uri.startswith('calmradio:'):
			return None

		variant, identifier = self.parse_uri(uri)

		if variant == 'track':
			chan_data = self.backend.calmradio.get_channel_by_id(identifier)

			track = Track(
				name = chan_data['title'].title(),
				comment = chan_data['description'],
				uri = 'calmradio:track:%s' % (identifier))

			return [track]

		return []


	def browse(self, uri):
		self.backend.refresh()

		directories = []
		tracks = []
		variant, identifier = self.parse_uri(uri)
		if variant == 'root':
			if self.backend.calmradio.categories:
				for genre in self.backend.calmradio.categories:
					directories.append(
						self.ref_directory(
							"calmradio:genre:" + str(genre['id']), genre['name'])
					)
		elif variant == 'genre' and identifier:
			if self.backend.calmradio.categories:
				genre_cats = self.backend.calmradio.get_genre_cats(identifier)
				for cat in genre_cats:
					directories.append(
						self.ref_directory(
							"calmradio:category:" + str(cat['id']), cat['name'].title())
					)
		elif variant == 'category' and identifier:
			if self.backend.calmradio.channels:
				cat_chans = self.backend.calmradio.get_cat_chans(identifier)
				for chan in cat_chans:
					tracks.append(self.channel_to_ref(identifier, chan))
		else:
			logger.debug('Unknown URI: %s', uri)
			return []

		tracks.sort(key=lambda ref: ref.name)

		return directories + tracks

	def get_images(self, uris):
		results = {}
		for uri in uris:
			variant, identifier = self.parse_uri(uri)
			if variant != "track":
				continue
			chan_data = self.backend.calmradio.get_channel_by_id(identifier)
			url = self.backend.calmradio.urls['calm_arts_host'] + chan_data['image']
			image = Image(uri = url)
			if image is not None:
				results[uri] = [image]
		return results


	def search(self, query=None, uris=None, exact=False):

		result = []

		self.backend.calmradio.do_search(' '.join(query['any']))

		for channel in self.backend.calmradio.search_results:
			result.append(self.channel_to_track(channel))

		return SearchResult(
			tracks = result
		)


	def channel_to_ref(self, catid, channel):
		return Ref.track(
			uri = 'calmradio:track:%s' % (catid + 'c' + str(channel['id'])),
			name = channel['title'].title(),
		)


	def channel_to_track(self, channel):
		ref = self.channel_to_ref(str(channel['catid']), channel)
		return Track(uri=ref.uri, name=ref.name)


	def ref_directory(self, uri, name):
		return Ref.directory(uri=uri, name=name)


	def parse_uri(self, uri):
		result = re.findall(r'^calmradio:([a-z]+):?([a-z0-9]+|\d+)?$', uri)
		if result:
			return result[0]
		return None, None
