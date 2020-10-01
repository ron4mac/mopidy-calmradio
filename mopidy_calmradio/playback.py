import logging

from mopidy import backend

logger = logging.getLogger(__name__)

handler = logging.FileHandler('var/log/mopidy/calmradio.log')
formatter = logging.Formatter('%(asctime)s %(name)-12s %(levelname)-8s %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(logging.DEBUG)

class CalmRadioPlayback(backend.PlaybackProvider):
	def translate_uri(self, uri):
		logger.debug('Translate URI: %s' % uri)
		track_id = uri.rsplit(":")[-1]
		chan_data = self.backend.calmradio.get_channel_by_id(track_id)
		token = self.backend.usertoken

		if token:
			bitrate = '320'
		else:
			bitrate = 'free_128'

		streams = chan_data.get('streams')
		
		if not token and bitrate in streams:
			logger.debug('Stream URL: %s' % streams[bitrate])
			return streams[bitrate]
		elif token:
			logger.debug('Stream URL: %s' % streams[bitrate])
			return streams[bitrate].replace('http://', 'http://{0}:{1}@'.format(
				self.backend.username,
				token
			))

		return None
