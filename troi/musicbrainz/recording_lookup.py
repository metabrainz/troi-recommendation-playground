from collections import defaultdict
from time import sleep

import requests
import ujson

from troi import Element, Artist, ArtistCredit, PipelineError, Recording, Playlist, Release


class RecordingLookupElement(Element):
    '''
        Look up a musicbrainz data for a list of recordings, based on MBID.

        :param skip_not_found: If skip_not_found is set to True (the default) then Recordings that cannot be found in MusicBrainz will not be returned from this Element.
    '''

    SERVER_URL = "https://api.listenbrainz.org/1/metadata/recording"
    MAX_RECORDINGS = 1000

    def __init__(self, skip_not_found=True, lookup_tags=False, tag_threshold=None, auth_token=None):
        Element.__init__(self)
        self.skip_not_found = skip_not_found
        self.lookup_tags = lookup_tags
        self.tag_threshold = tag_threshold
        self.auth_token = auth_token

    @staticmethod
    def inputs():
        return [ Recording, Playlist ]

    @staticmethod
    def outputs():
        return [ Recording, Playlist ]

    def read(self, inputs):

        if isinstance(inputs[0], Playlist):
            recordings = inputs[0].recordings
        else:
            recordings = inputs[0]
        if not recordings:
            return []

        recording_mbids = []
        for r in recordings:
            recording_mbids.append(r.mbid)

        if len(recording_mbids) > self.MAX_RECORDINGS:
            raise PipelineError("Cannot fetch more than %d recordings from ListenBrainz." % self.MAX_RECORDINGS)

        inc = "artist release"
        if self.lookup_tags:
            inc += " tag"

        while True:
            headers = {"Authorization": f"Token {self.auth_token}"} if self.auth_token else {}
            r = requests.post(self.SERVER_URL, json={"recording_mbids": recording_mbids, "inc": inc}, headers=headers)
            if r.status_code == 429:
                sleep(2)
                continue

            if r.status_code != 200:
                raise PipelineError("Cannot fetch recordings from ListenBrainz: HTTP code %d (%s)" % (r.status_code, r.text))

            break

        try:
            data = ujson.loads(r.text)
        except ValueError as err:
            raise PipelineError("Cannot parse recordings: " + str(err))

        output = []
        for r in recordings:
            # Check if some tracks didn't resolve
            try:
                metadata_recording = data[r.mbid]
            except KeyError:
                if not self.skip_not_found:
                    output.append(r)
                continue

            if self.lookup_tags:
                # Parcel out the tags for artists
                artist_genres = defaultdict(list)
                artist_tags = defaultdict(list)
                for genre in data[r.mbid]["tag"]["artist"]:
                    if "genre_mbid" in genre:
                        artist_genres[genre["artist_mbid"]].append(genre["tag"])
                    else:
                        artist_tags[genre["artist_mbid"]].append(genre["tag"])

            # Now build the artists
            artists = []
            for artist in metadata_recording["artist"]["artists"]:
                artists.append(Artist(mbid=artist["artist_mbid"], 
                                      name=artist["name"],
                                      join_phrase=artist["join_phrase"]))


            # Now that we have artists, we can build artist credits.
            r.artist_credit = ArtistCredit(name=metadata_recording["artist"]["name"],
                                           artists=artists,
                                           artist_credit_id=metadata_recording["artist"]['artist_credit_id'])

            if self.lookup_tags:
                # Finish this, read from dict above
                r.artist_credit.musicbrainz["genre"] = artist_genres[artist["artist_mbid"]]
                r.artist_credit.musicbrainz["tag"] = artist_tags[artist["artist_mbid"]]

            if metadata_recording["release"]:
                # Now create the release data
                r.release = Release(name=metadata_recording["release"]["name"],
                                    mbid=metadata_recording["release"]["mbid"],
                                    caa_id=metadata_recording["release"].get("caa_id", None),
                                    caa_release_mbid=metadata_recording["release"].get("caa_release_mbid", None),
                                    musicbrainz={"release_group_mbid":metadata_recording["release"]["release_group_mbid"]})
            else:
                r.release = None

            if self.lookup_tags:
                # Process the release tags
                genres = []
                tags = []
                for genre in data[r.mbid]["tag"]["release_group"]:
                    if "genre_mbid" in genre:
                        genres.append(genre["tag"])
                    else:
                        tags.append(genre["tag"])

                r.release.musicbrainz = { "genre": genres, "tag": tags }

            # Finally copy data for the recording itself
            r.name = metadata_recording["recording"]['name']
            try:
                r.duration = metadata_recording["recording"]['length']
            except KeyError:
                pass
            try:
                r.year = metadata_recording["release"]["year"]
            except KeyError:
                pass

            if self.lookup_tags:
                # Process the recording tags
                genres = []
                tags = []
                for genre in data[r.mbid]["tag"]["recording"]:
                    if "genre_mbid" in genre:
                        genres.append(genre["tag"])
                    else:
                        tags.append(genre["tag"])

                r.musicbrainz = { "genre": genres, "tag": tags }

            output.append(r)

        if isinstance(inputs[0], Playlist):
            inputs[0].recordings = output
            output = inputs[0]

        return output
