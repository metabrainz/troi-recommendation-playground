import json
import requests
from troi import Element, Recording, PipelineError
import liblistenbrainz
import liblistenbrainz.errors
import dateutil.parser

MAX_NUM_RECORDINGS_PER_REQUEST = 100


class UserRecordingRecommendationsElement(Element):
    '''
        Fetch recommended recordings for a user from ListenBrainz.

        :param user_name: The ListenBrainz user to fetch recs for.
        :param artist_type: The type of recs to fetch. Must be one of "top", "similar" or "raw".
        :param count: The number of recs to fetch. Defaults to 25.
    '''

    MAX_RECORDINGS_TO_FETCH = 2000

    def __init__(self, user_name, artist_type, count=25, offset=0, auth_token=None):
        super().__init__()
        self.client = liblistenbrainz.ListenBrainz()
        if auth_token is not None:
            self.client.set_auth_token(auth_token)
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

        remaining = self.MAX_RECORDINGS_TO_FETCH if self.count < 0 else self.count
        while True:
            try:
                recordings = self.client.get_user_recommendation_recordings(self.user_name, 
                                                                            self.artist_type, 
                                                                            count=min(MAX_NUM_RECORDINGS_PER_REQUEST, remaining),
                                                                            offset=self.offset+len(recording_list))
            except (requests.exceptions.HTTPError,
                    liblistenbrainz.errors.ListenBrainzAPIException,
                    requests.exceptions.ConnectionError) as err:
                if not str(err):
                    err = "Does the user '%s' exist?" % self.user_name
                raise PipelineError("Cannot fetch recommeded tracks from ListenBrainz: " + str(err))

            if not recordings or not len(recordings['payload']['mbids']):
                break

            for r in recordings['payload']['mbids']:
                latest = r.get("latest_listened_at", None)
                if latest is not None:
                    latest = dateutil.parser.isoparse(latest)
                    latest = latest.replace(tzinfo=None)
                lb_metadata = { "model_id": recordings["payload"].get("model_id", None),
                                "model_url": recordings["payload"].get("model_url", None),
                                "latest_listened_at": latest }
                recording_list.append(Recording(mbid=r['recording_mbid'], ranking=r['score'], listenbrainz=lb_metadata))

            remaining -= len(recordings['payload']['mbids'])
            if remaining <= 0:
                break

        if recordings:
            self._last_updated = recordings['payload']['last_updated']

        return recording_list
