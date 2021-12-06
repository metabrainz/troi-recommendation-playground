import requests
import ujson

from troi import Element, Recording, PipelineError


class GenreLookupElement(Element):
    """
        Look up musicbrainz tags for a list of recordings recordings, based on recording mbid.
        Mosly for experimentation for now -- still needs support for adding genre vs tag.
    """

    SERVER_URL = "http://bono.metabrainz.org:8000/genre-mbid-lookup/json"

    def __init__(self):
        Element.__init__(self)

    @staticmethod
    def inputs():
        return [Recording]

    @staticmethod
    def outputs():
        return [Recording]

    def read(self, inputs):

        recordings = inputs[0]
        if not recordings:
            return []

        data = []
        for r in recordings:
            data.append({'[recording_mbid]': r.mbid})

        r = requests.post(self.SERVER_URL, json=data)
        if r.status_code != 200:
            raise PipelineError("Cannot fetch recording tags from MusicBrainz: HTTP code %d" % r.status_code)

        try:
            rows = ujson.loads(r.text)
        except ValueError as err:
            raise PipelineError("Cannot fetch recording tags from MusicBrainz: " + str(err))

        mbid_index = {}
        for row in rows:
            mbid_index[row['recording_mbid']] = row["tags"]

        output = []
        for r in recordings:
            try:
                r.musicbrainz["tags"] = mbid_index[r.mbid]
            except KeyError:
                self.debug("recording (%s) not found, skipping." % r.mbid)
                continue

            output.append(r)

        return output
