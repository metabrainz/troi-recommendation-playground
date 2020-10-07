import datetime

import requests
import ujson
from troi import Element, Artist, Release, Recording
import pylistenbrainz


class UserRecordingRecommendationsElement(Element):
    '''
        Fetch recommended recording for a user from ListenBrainz
    '''

    MAX_RECORDINGS_PER_REQUEST = 100
    MAX_RECORDINGS = 200

    def __init__(self, user_name, artist_type, count=25, offset=0):
        """
            The offset parameter does not work yet.
        """
        Element.__init__(self)
        self.client = pylistenbrainz.ListenBrainz()
        self.user_name = user_name
        self.count = count
        self.offset = offset
        self.artist_type = artist_type
        self._last_updated = None

    def outputs(self):
        return [Recording]

    @property
    def last_updated(self):
        return self._last_updated

    def read(self, inputs = []):
        recording_list = []
        recordings = []

        while True:
            recordings = self.client.get_user_recommendation_recordings(self.user_name, 
                                                                        self.artist_type, 
                                                                        count=self.count - len(recording_list),
                                                                        offset=len(recording_list))

            if not len(recordings['payload']['mbids']):
                break

            for r in recordings['payload']['mbids']:
                recording_list.append(Recording(mbid=r['recording_mbid'], listenbrainz={'score':r['score']}))

            if len(recording_list) >= self.count:
                break

        self._last_updated = datetime.datetime.fromtimestamp(recordings['payload']['last_updated'])

        return recording_list
