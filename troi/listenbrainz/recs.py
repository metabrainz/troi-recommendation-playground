import requests
import ujson
from troi import Element, Artist, Release, Recording
import pylistenbrainz

MAX_NUM_RECORDINGS_PER_REQUEST = 100


class UserRecordingRecommendationsElement(Element):
    '''
        Fetch recommended recording for a user from ListenBrainz
    '''

    def __init__(self, user_name, artist_type, count=25, offset=0):
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

    def read(self, inputs = [], debug=False):
        recording_list = []
        recordings = []

        while True:
            try:
                recordings = self.client.get_user_recommendation_recordings(self.user_name, 
                                                                            self.artist_type, 
                                                                            count=MAX_NUM_RECORDINGS_PER_REQUEST,
                                                                            offset=self.offset+len(recording_list))
            except requests.exceptions.HTTPError as err:
                raise RuntimeError(err)

            if not len(recordings['payload']['mbids']):
                break

            for r in recordings['payload']['mbids']:
                recording_list.append(Recording(mbid=r['recording_mbid'], ranking=r['score']))

            if self.count > 0 and len(recording_list) >= self.count:
                break

        self._last_updated = recordings['payload']['last_updated']

        return recording_list
