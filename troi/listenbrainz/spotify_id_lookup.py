import requests
import ujson

from troi import Element, Artist, Recording, PipelineError

class SpotifyIdLookupElement(Element):
    '''
        Lookup recordings
    '''

    SERVER_URL = "https://labs.api.listenbrainz.org/spotify-id-from-mbid/json"

    def __init__(self):
        super().__init__()

    @staticmethod
    def inputs():
        return [ Recording ]

    @staticmethod
    def outputs():
        return [ Recording ]

    def read(self, inputs):

        mbids = [ { "[recording_mbid]": r.mbid } for r in inputs[0] ]

        r = requests.post(self.SERVER_URL, json=mbids)
        if r.status_code != 200:
            raise PipelineError("Cannot fetch spotify IDs from ListenBrainz. HTTP code %s" % r.status_code)

        spotify_index = {}
        for item in r.json():
            try:
                spotify_index[item["recording_mbid"]] = item["spotify_track_ids"][0]
            except IndexError:
                continue

        recordings = []
        for recording in inputs[0]:
            try:
                recording.listenbrainz["spotify_id"] = spotify_index[recording.mbid]
            except KeyError:
                continue    

            recordings.append(recording)

        return recordings
