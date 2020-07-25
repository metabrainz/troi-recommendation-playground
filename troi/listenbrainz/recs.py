
import requests
import ujson
from troi import Element, Artist, Release, Recording
import pylistenbrainz


class UserRecordingRecommendationsElement(Element):
    '''
        Fetch recommended recording for a user from ListenBrainz
    '''

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

    def outputs(self):
        return [Recording]

    def read(self, inputs = []):
        recording_list = []
        recordings = self.client.get_user_recommendation_recordings(self.user_name, self.artist_type, self.count, self.offset)

        artist_type = self.artist_type + "_artist"  
        for r in recordings['payload'][artist_type]['recording_mbid']:
            recording_list.append(Recording(mbid=r))

        return recording_list
