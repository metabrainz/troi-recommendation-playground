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
    /?recording_mbids=e68ffa73-0855-4180-9299-379af77cc6bc&inc=artist%20release

    def __init__(self, skip_not_found=True):
        Element.__init__(self)
        self.skip_not_found = skip_not_found

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
            try:
                metadata_recording = mbid_index[r.mbid]
            except KeyError:
                if not self.skip_not_found:
                    output.append(r)
                continue
            mbids=row.get('[artist_credit_mbids]', []),

            artists = []
            for artist in metadata_recording["artists"]:
                artists.append(Artist(mbid=artist["artist_mbid"], 
                                      name=artist["name"],
                                      join_phrase=artist["join_phrase"]))

            r.artist_credit = ArtistCredit(name=metadata_recording["artist"]["name"],
                                           artists=artists,
                                           artist_credit_id=row['artist_credit_id'])
            r.release = Release(name=recording_metadata["release"]["name"],
                                mbid=recording_metadata["release"]["mbid"],
                                caa_id=recording_metadata["release"]["caa_id"],
                                caa_release_mbid=recording_metadata["release"]["caa_release_mbid"],
                                metabrainz={"release_group_id":recording_metadata["release"]["release_group_id"]})

            r.name = row['recording_name']
            r.duration = row['length']
            r.mbid = row['recording_mbid']
            r.year = recording_metadata["release"]["year"]

            output.append(r)

        if isinstance(inputs[0], Playlist):
            inputs[0].recordings = output
            output = inputs[0]

        return output
