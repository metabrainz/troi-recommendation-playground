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

        self.local_storage["_playlist_name"] = "%s artist discovery playlist" % data["name"]
        self.local_storage["_playlist_desc"] = "Discover artists that are playing at %s. This playlist " % data["name"] + \
                                               "contains one track by each of the artists playing at the festival. " +  \
                                               "Hopefully this playlist allows you to plan your festival better!"

        return result


class FestivalTracksElement(Element):
    '''
    '''

    def __init__(self, ptype):
        super().__init__()
        self.ptype = ptype

    @staticmethod
    def inputs():
        return [ArtistCredit]

    @staticmethod
    def outputs():
        return [Recording]

    def get_album_recording(self, artist_mbid):

        print("Get album track for %s" % artist_mbid)
        while True:
            r = requests.get("https://musicbrainz.org/ws/2/artist/%s/?fmt=json&inc=releases" % artist_mbid)
            if r.status_code == 503:
                sleep(2)
                continue

            if r.status_code == 404:
                print("No albums for %s" % artist_mbid)
                return None

            if r.status_code != 200:
                raise PipelineError("Cannot find artist %s: %s" % (artist_mbid, r.text))
            else:
                break

        releases = r.json()["releases"]
        releases = sorted(releases, key=lambda a: a.get("date", "000"), reverse=True)

        try:
            release_mbid = releases[0]["id"]
        except IndexError:
            print("Found no releases for artist %s" % artist_mbid)
            return None

        while True:
            r = requests.get("https://musicbrainz.org/ws/2/release/%s/?fmt=json&inc=recordings" % release_mbid)
            if r.status_code == 503:
                sleep(2)
                continue

            if r.status_code == 404:
                print("Couldn't find release %s" % release_mbid)
                return None

            if r.status_code != 200:
                raise PipelineError("Cannot find release %s: %s" % (release_mbid, r.text))
            else:
                break

        tracks = plist(r.json()["media"][0]["tracks"])
        track = tracks.random_item()

        return Recording(mbid=track["recording"]["id"], name=track["title"])


    def read(self, inputs):

        recordings = []
        for artist in inputs[0]:
            artist_mbid = artist.artists[0].mbid
            print("process %s" % artist_mbid)

            if self.ptype == "top":
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
            else:
                data = None

            if not data:
                rec = self.get_album_recording(artist_mbid)
                if rec:
                    recordings.append(rec)
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
        TYPE: The type of festival playlist to generate. Must be "recent" to create a playlist
              from recent releases by artists or "top" to create a playlist that contains
              popular tracks for the artists.
        EVENT_MBID: The MBID of the festival event.
        """
        return [
            {"type": "argument", "args": ["type"]},
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
        ptype = inputs['type']
        event_mbid = inputs['event_mbid']

        if ptype not in ("top", "recent"):
            raise RuntimeError("Festival playlist type must be either 'top' or 'recent'")

        f_playlist = FestivalPlaylistElement(event_mbid)

        popular = FestivalTracksElement(ptype)
        popular.set_sources(f_playlist)

        rec_lookup = RecordingLookupElement()
        rec_lookup.set_sources(popular)

        pl_maker = PlaylistMakerElement(shuffle=True)
        pl_maker.set_sources(rec_lookup)

        return pl_maker
