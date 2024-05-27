from time import sleep

from troi import Element, Recording, Playlist, PipelineError, Artist, ArtistCredit
from troi.musicbrainz.recording_lookup import RecordingLookupElement
from troi.playlist import PlaylistMakerElement
from troi.patch import Patch
from troi.plist import plist

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
        return [ArtistCredit]

    def read(self, inputs):

        r = requests.get("https://musicbrainz.org/ws/2/event/%s?fmt=json&inc=artist-rels" % self.event_mbid)
        if r.status_code != 200:
            raise PipelineError("Cannot find festival %s: %s" % (self.event_mbid, r.text))

        data = r.json()

        artist_mbids = [r["artist"]["id"] for r in data["relations"] ]
        result = []
        for artist_mbid in artist_mbids:
            artists = [ Artist(mbid=artist_mbid) ]
            result.append(ArtistCredit(artists=artists))

        return result


class PopularTracksElement(Element):
    '''
    '''

    @staticmethod
    def inputs():
        return [ArtistCredit]

    @staticmethod
    def outputs():
        return [Recording]

    def read(self, inputs):

        recordings = []
        for artist in inputs[0]:
            artist_mbid = artist.artists[0].mbid
            while True:
                r = requests.get("https://api.listenbrainz.org/1/popularity/top-recordings-for-artist/%s" % artist_mbid)
                if r.status_code == 429:
                    sleep(2)
                    continue

                if r.status_code == 404:
                    print("No top tracks for %s" % artist_mbid)
                    continue

                if r.status_code != 200:
                    raise PipelineError("Cannot find artist %s: %s" % (artist_mbid, r.text))
                else:
                    break

            data = plist(r.json()[:10])
            if not data:
                print("No top data for artist: %s" % artist_mbid)
                continue

            
            recording = data.random_item()
            recordings.append(Recording(mbid=recording["recording_mbid"], name=recording["recording_name"]))
            print(recording["artist_name"])

        return recordings


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

        popular = PopularTracksElement()
        popular.set_sources(f_playlist)

        rec_lookup = RecordingLookupElement()
        rec_lookup.set_sources(popular)

        pl_maker = PlaylistMakerElement(name="Festival playlist",
                                        desc="festival",
                                        shuffle=True)
        pl_maker.set_sources(rec_lookup)

        return pl_maker
