from datetime import datetime

import requests

from troi import Element, Recording, Artist, PipelineError


class FetchListensElement(Element):
    """
        Load listens for a user from ListenBrainz.
    """

    SERVER_URL = "https://api.listenbrainz.org/1/%s/listens?max_ts=%d"

    def __init__(self, user_name):
        Element.__init__(self)
        self.user_name = user_name

    @staticmethod
    def inputs():
        return []

    @staticmethod
    def outputs():
        return [Recording]

    def read(self, inputs):

        dt = datetime.utcnow()
        dt = datetime(year=dt.year, month=dt.month, day=dt.day, hour=0, minute=0)
        to_ts = int(dt.timestamp())

        r = requests.get(self.SERVER_URL % (self.user_name, to_ts))
        if r.status_code != 200:
            raise PipelineError("Cannot fetch recording tags from MusicBrainz: HTTP code %d" % r.status_code)


        output = []
        for listen in r.json()["payload"]["listens"]:
            try:
                a = Artist(mbids=listen["track_metadata"]["mbid_mapping"]["artist_mbids"],
                           name=listen["track_metadata"]["artist"])
                r = Recording(mbid=listen["track_metadata"]["mbid_mapping"]["recording_mbid"],
                              name=listen["track_metadata"]["track_name"],
                              artist=a)
                output.append(r)
            except KeyError:
                pass

        return output
