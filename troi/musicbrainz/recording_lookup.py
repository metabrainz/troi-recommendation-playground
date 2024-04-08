from collections import defaultdict
from time import sleep

import requests
import ujson

from troi import Element, Artist, PipelineError, Recording, Playlist, Release


class RecordingLookupElement(Element):
    '''
        Look up a musicbrainz data for a list of recordings, based on MBID.

        :param skip_not_found: If skip_not_found is set to True (the default) then Recordings that cannot be found in MusicBrainz will not be returned from this Element.
    '''

    SERVER_URL = "https://api.listenbrainz.org/1/metadata/recording"

    def __init__(self, skip_not_found=True, lookup_tags=False, tag_threshold=None):
        Element.__init__(self)
        self.skip_not_found = skip_not_found
        self.lookup_tags = lookup_tags
        self.tag_threshold = tag_threshold

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
            if r.artist is None or r.artist.name is None or len(r.artist.mbids) == 0 or r.name is None:
                recording_mbids.append(r.mbid)

        # If we have all the data for all the recordings, no need to lookup anything and simply pass the data along
        if len(data) == 0:
            return inputs[0]

        inc = "artist release"
        if self.lookup_tags:
            inc += " tag"

        while True:
            r = requests.get(self.SERVER_URL, params={"recording_mbids": recording_mbids, "inc": "artist release"})
            if r.status_code == 429:
                sleep(2)
                continue

            if r.status_code != 200:
                raise PipelineError("Cannot fetch recordings from ListenBrainz: HTTP code %d (%s)" % (r.status_code, r.text))

            break

        try:
            data = ujson.loads(r.text)
        except ValueError as err:
            raise PipelineError("Cannot fetch recordings from ListenBrainz: " + str(err))

        output = []
        for r in recordings:
            # Check if some tracks didn't resolve
            try:
                metadata_recording = mbid_index[r.mbid]
            except KeyError:
                if not self.skip_not_found:
                    output.append(r)
                continue

            # Parcel out the tags for artists
            artist_genres = defaultdict(list)
            artist_tags = defaultdict(list)
            for genre in data[r.mbid]["tag"]["artist"]:
                if genre["count"] >= self.count_threshold:
                    if "genre_mbid" in genre:
                        artist_genres[genre["artist_mbid"]].append(genre["tag"])
                    else:
                        artist_tags[genre["artist_mbid"]].append(genre["tag"])

            # Now build the artists
            artists = []
            for artist in metadata_recording["artists"]:
                artists.append(Artist(mbid=artist["artist_mbid"], 
                                      name=artist["name"],
                                      join_phrase=artist["join_phrase"]))

                # Finish this, read from dict above
                r.artist.musicbrainz["genre"] = artist_genres[artist["artist_mbid"]]
                r.artist.musicbrainz["tag"] = artist_tags[artist["artist_mbid"]]

            # Now that we have artists, we can build artist credits.
            r.artist_credit = ArtistCredit(name=metadata_recording["artist"]["name"],
                                           artists=artists,
                                           artist_credit_id=row['artist_credit_id'])

            # Now create the release data
            r.release = Release(name=recording_metadata["release"]["name"],
                                mbid=recording_metadata["release"]["mbid"],
                                caa_id=recording_metadata["release"]["caa_id"],
                                caa_release_mbid=recording_metadata["release"]["caa_release_mbid"],
                                metabrainz={"release_group_id":recording_metadata["release"]["release_group_id"]})

            # Finally copy data for the recording itself
            r.name = row['recording_name']
            r.duration = row['length']
            r.mbid = row['recording_mbid']
            r.year = recording_metadata["release"]["year"]

            # Process the recording tags
            genres = []
            tags = []
            for genre in metadata_recording[r.mbid]["tag"]["recording"]:
                if genre["count"] >= self.tag_threshold:
                    if "genre_mbid" in genre:
                        genres.append(genre["tag"])
                    else:
                        tags.append(genre["tag"])

            r.musicbrainz["genre"] = genres
            r.musicbrainz["tag"] = tags

            output.append(r)

        if isinstance(inputs[0], Playlist):
            inputs[0].recordings = output
            output = inputs[0]

        return output
