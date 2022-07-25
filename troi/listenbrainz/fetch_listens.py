from datetime import datetime

import requests

from troi import Element, Recording, Artist, User, PipelineError


class FetchListensElement(Element):
    """
        Load listens for a user from ListenBrainz.
    """

    SERVER_URL = "https://api.listenbrainz.org/1/user/%s/listens"
    MIN_LISTENS_TO_FETCH = 200

    def __init__(self):
        Element.__init__(self)

    @staticmethod
    def inputs():
        return [User]

    @staticmethod
    def outputs():
        return [Recording]

    def read(self, inputs):

        users = inputs[0]

        dt = datetime.utcnow()
        dt = datetime(year=dt.year, month=dt.month, day=dt.day, hour=0, minute=0)
        print(dt)
        to_ts = int(dt.timestamp())
        from_ts = to_ts - (60 * 60 * 24)
        print(from_ts, to_ts)

        count = 0
        recording_sets = []
        for user in users:
            print(user.user_name)

            r = requests.get(self.SERVER_URL % user.user_name, params={ "max_ts":to_ts, "min_ts":from_ts})
            print(r.url)
            if r.status_code != 200:
                raise PipelineError("Cannot fetch listens from MusicBrainz: HTTP code %d" % r.status_code, r.text)

            recordings = []
            for listen in r.json()["payload"]["listens"]:
                try:
                    a = Artist(mbids=listen["track_metadata"]["mbid_mapping"]["artist_mbids"],
                               name=listen["track_metadata"]["artist_name"])
                    r = Recording(mbid=listen["track_metadata"]["mbid_mapping"]["recording_mbid"],
                                  name=listen["track_metadata"]["track_name"],
                                  artist=a)
                    recordings.append(r)
                except KeyError as err:
                    print(err)

            self.debug("Fetched %d listens" % len(recordings))
            count += len(recordings)
            if len(recordings) > 0:
                recording_sets.append(recordings)
                recordings = 0

            if count > FetchListensElement.MIN_LISTENS_TO_FETCH:
                break

        self.debug("Fetched %d listens total" % count)

        return recording_sets
