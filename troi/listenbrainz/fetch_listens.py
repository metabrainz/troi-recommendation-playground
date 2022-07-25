from datetime import datetime

import requests

from troi import Element, Recording, Artist, User, PipelineError


class FetchListensElement(Element):
    """
        Load listens for a user from ListenBrainz.
    """

    SERVER_URL = "https://api.listenbrainz.org/1/user/%s/listens"
    MIN_LISTENS_TO_FETCH = 200

    def __init__(self, min_ts, max_ts):
        Element.__init__(self)
        self.min_ts = min_ts
        self.max_ts = max_ts

    @staticmethod
    def inputs():
        return [User]

    @staticmethod
    def outputs():
        return [Recording]

    def read(self, inputs):

        users = inputs[0]

        count = 0
        recordings = []
        for user in users:
            r = requests.get(self.SERVER_URL % user.user_name, params={ "max_ts":self.max_ts, "min_ts":self.min_ts})
            if r.status_code != 200:
                raise PipelineError("Cannot fetch listens from MusicBrainz: HTTP code %d" % r.status_code, r.text)

            for listen in r.json()["payload"]["listens"]:
                try:
                    a = Artist(mbids=listen["track_metadata"]["mbid_mapping"]["artist_mbids"],
                               name=listen["track_metadata"]["artist_name"])
                    r = Recording(mbid=listen["track_metadata"]["mbid_mapping"]["recording_mbid"],
                                  name=listen["track_metadata"]["track_name"],
                                  artist=a,
                                  musicbrainz={ "user": user.user_name })
                    recordings.append(r)
                except KeyError as err:
                    print(err)

            self.debug("Fetched %d listens %s total" % (len(recordings), count))
            count += len(recordings)
            if count > FetchListensElement.MIN_LISTENS_TO_FETCH:
                break

        self.debug("Fetched %d listens total" % count)

        return recordings
