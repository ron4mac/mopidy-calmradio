import time

from mopidy import backend

import pykka

import mopidy_calmradio

from .library import CalmRadioLibraryProvider
from .calmradio import CalmRadioClient
from .playback import CalmRadioPlayback


class CalmRadioBackend(pykka.ThreadingActor, backend.Backend):

	update_timeout = None
	username = None
	password = None
	usertoken = None

	def __init__(self, config, audio):
		super(CalmRadioBackend, self).__init__()
		self.calmradio = CalmRadioClient(
			config['proxy'],
			"%s/%s" % (
				mopidy_calmradio.Extension.dist_name,
				mopidy_calmradio.__version__))

		self.library = CalmRadioLibraryProvider(backend=self)
		self.playback = CalmRadioPlayback(audio=audio, backend=self)

		self.uri_schemes = ['calmradio']
		self.username = config['calmradio']['username']
		self.password = config['calmradio']['password']
		self.usertoken = self.calmradio.authenticate(self.username, self.password)

		self.calmradio.min_bitrate = int(config['calmradio']['min_bitrate'])


	def set_update_timeout(self, minutes=120):
		self.update_timeout = time.time() + 60 * minutes


	def on_start(self):
		self.set_update_timeout(0)


	def refresh(self, force=False):
		if self.update_timeout is None:
			self.set_update_timeout()

		if force or time.time() > self.update_timeout:
			self.calmradio.get_categories()
			self.calmradio.get_channels()
			self.set_update_timeout()
