from troi import Element, Recording, Playlist, PipelineError
from troi.musicbrainz.recording_lookup import RecordingLookupElement
from troi.playlist import PlaylistMakerElement
from troi.patch import Patch

import requests


class FestivalPlaylistElement(Element):
    '''
    '''

    def __init__(self, event_mbid):
        super().__init__()
        self.event_mbid = event_mbid

    @staticmethod
    def inputs():
        return []

    @staticmethod
    def outputs():
        return [Recording]

    def read(self, inputs):

        r = requests.get("https://musicbrainz.org/ws/2/event/%s?fmt=json&inc=artist-rels" % self.event_mbid)
        if r.status_code != 200:
            raise PipelineError("Cannot find festival %s: %s" % (self.event_mbid, r.text))

        data = r.json()
        import json
        print(json.dumps(data, indent=2))

        artist_mbids = [r["artist"]["id"]) for r in data["relations"]
        for artist_mbid
        r = requests.get("https://musicbrainz.org/ws/2/event/%s?fmt=json&inc=artist-rels" % self.event_mbid)
        if r.status_code != 200:
            raise PipelineError("Cannot find festival %s: %s" % (self.event_mbid, r.text))


class FestivalPlaylistPatch(Patch):
    """
        See below for description
    """

    def __init__(self, args):
        super().__init__(args)

    @staticmethod
    def inputs():
        """
        Save the current recommended tracks for a given user and type (top or similar).

        \b
        EVENT_MBID: The MBID of the festival event.
        """
        return [
            {"type": "argument", "args": ["event_mbid"]}
        ]

    @staticmethod
    def outputs():
        return [Recording]

    @staticmethod
    def slug():
        return "festival-playlist"

    @staticmethod
    def description():
        return "Create a festival playlist from a MusicBrainz event."

    def create(self, inputs):
        event_mbid = inputs['event_mbid']

        f_playlist = FestivalPlaylistElement(event_mbid)

        rec_lookup = RecordingLookupElement()
        rec_lookup.set_sources(f_playlist)

        pl_maker = PlaylistMakerElement(name="Festival playlist",
                                        desc="festival",
                                        shuffle=True)
        pl_maker.set_sources(rec_lookup)

        return pl_maker
