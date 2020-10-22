import requests
import ujson
from troi import Element, Artist, Release, Recording, PipelineError
import pylistenbrainz
import pylistenbrainz.errors

MAX_NUM_RECORDINGS_PER_REQUEST = 100


class UserRecordingRecommendationsElement(Element):
    '''
        Fetch recommended recording for a user from ListenBrainz
    '''

    MAX_RECORDINGS_TO_FETCH = 2000

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

        remaining = self.MAX_RECORDINGS_TO_FETCH if self.count < 0 else self.count
        while True:
            try:
                print("remaining: %d" % remaining)
                recordings = self.client.get_user_recommendation_recordings(self.user_name, 
                                                                            self.artist_type, 
                                                                            count=min(MAX_NUM_RECORDINGS_PER_REQUEST, remaining),
                                                                            offset=self.offset+len(recording_list))
            except (requests.exceptions.HTTPError, pylistenbrainz.errors.ListenBrainzAPIException) as err:
                if not str(err):
                    err = "Does the user '%s' exist?" % self.user_name
                raise PipelineError("Cannot fetch recommeded tracks from ListenBrainz: " + str(err))

            print(recordings)
            if not recordings or not len(recordings['payload']['mbids']):
                break

            for r in recordings['payload']['mbids']:
                recording_list.append(Recording(mbid=r['recording_mbid'], ranking=r['score']))

            remaining -= len(recording_list)
            if remaining <= 0:
                break

        if recordings:
            self._last_updated = recordings['payload']['last_updated']

        return recording_list
