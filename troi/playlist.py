from collections import defaultdict
from operator import attrgetter
import json
import requests

from troi import Recording, Playlist, PipelineError, Element
from troi.operations import is_homogeneous
from troi.print_recording import PrintRecordingList

LISTENBRAINZ_SERVER_URL = "https://api.listenbrainz.org"
LISTENBRAINZ_PLAYLIST_CREATE_URL = LISTENBRAINZ_SERVER_URL + "/1/playlist/create"
PLAYLIST_TRACK_URI_PREFIX = "https://musicbrainz.org/recording/"
PLAYLIST_ARTIST_URI_PREFIX = "https://musicbrainz.org/artist/"
PLAYLIST_RELEASE_URI_PREFIX = "https://musicbrainz.org/release/"
PLAYLIST_URI_PREFIX = "https://listenbrainz.org/playlist/"
PLAYLIST_EXTENSION_URI = "https://musicbrainz.org/doc/jspf#playlist"

def _serialize_to_jspf(playlist, created_for=None, track_count=None, algorithm_metadata=None):
    """
        Serialize a playlist to JSPF.

        Arguments:
            created_for: The user name of the user for whom this playlist
                         was created.
            track_count: The number of tracks to serialize. If not provided,
                         all tracks will be serialized.
    """

    data = { "creator": "ListenBrainz Troi",
             "extension": {
                 PLAYLIST_EXTENSION_URI: {
                     "public": True
                 }
           }
    }

    if playlist.name:
        data["title"] = playlist.name

    if playlist.description:
        data["annotation"] = playlist.description

    if created_for:
        data["extension"][PLAYLIST_EXTENSION_URI]["created_for"] = created_for

    if algorithm_metadata:
        data["extension"][PLAYLIST_EXTENSION_URI]["alogrithm_metadata"] = algorithm_metadata

    if not track_count or track_count < 0 or track_count > len(playlist.recordings):
        track_count = len(playlist.recordings)

    tracks = []
    for e in playlist.recordings[:track_count]:
        track = {}
        artist_mbids = [ str(mbid) for mbid in e.artist.mbids or [] ]
        track["creator"] = e.artist.name if e.artist else ""
        track["album"] = e.release.name if e.release else ""
        track["title"] = e.name
        track["identifier"] = "https://musicbrainz.org/recording/" + str(e.mbid)
        if artist_mbids:
            track["extension"] = {
                PLAYLIST_TRACK_URI_PREFIX: {
                    "artist_mbids" : artist_mbids,
                }
            }
        tracks.append(track)

    data['track'] = tracks

    return { "playlist" : data }


class PlaylistElement(Element):
    """
        Take a list of Recordings or Playlists and save, print or submit them. The playlist element takes
        lists of recordings or lists of playlists and saves them to disk or submits them to ListenBrainz.

        This element can receive a list of recordings in which case that will be treated as a single
        playlist. This element can also recevied a list of playlists, in which case each playlist will
        be saved/submitted individually.

        Note that the Playlist entity object is distinct from this class -- the Playlist object tracks
        the core components of a playlist for passing through troi piplines, whereas this class
        is designed to be the end of the pipeline for saving results.
    """

    def __init__(self):
        super().__init__()
        self.playlists = []
        self.print_recording = PrintRecordingList()

    @staticmethod
    def inputs():
        return [Recording, Playlist]

    def __str__(self):
        return str(self.playlists)

    def read(self, inputs):

        for input in inputs:
            if len(input) == 0:
                print("No recordings or playlists generated to save.")
                continue

            if isinstance(input[0], Recording):
                if not is_homogeneous(input):
                    raise TypeError("entity list not homogeneous")
                self.playlists.append(Playlist(recordings=input))
            elif isinstance(input[0], Playlist):
                if not is_homogeneous(input):
                    raise TypeError("entity list not homogeneous")
                self.playlists.extend(input)
            else:
                raise PipelineError("Playlist passed incorrect input types.")

        return inputs[0]

    def print(self):
        """Prints the resultant playlists, one after another."""

        if not self.playlists:
            print("[no playlist(s) generated yet]")
            return

        for i, playlist in enumerate(self.playlists):
            if playlist.name:
                print("playlist: '%s'" % playlist.name)
            else:
                print("playlist: %d" % i)

            for recording in playlist.recordings:
                if not recording:
                    print("[invalid Recording]")
                    continue
                self.print_recording.print(recording)

    def save(self, track_count=None, algorithm_metadata=None, file_obj=None):
        """Save each playlist to disk, giving each playlist a unique name if none was provided.

           Arguments:
              track_count: If provided, write out only this many tracks to the playlist/
              algorithm_metadata: If provided, submit this dict of data with the playlist
                                  as part of the playlist metadata. 
              file_obj: If provided, write the JSPF file to this file_object
        """

        if not self.playlists:
            raise PipelineError("Playlists have not been generated yet.")

        for i, playlist in enumerate(self.playlists):
            if not file_obj:
                filename = playlist.filename or "playlist_%03d.jspf" % i
                with open(filename, "w") as f:
                    f.write(json.dumps(_serialize_to_jspf(playlist,
                                                          track_count=track_count,
                                                          algorithm_metadata=algorithm_metadata)))
            else:
                file_obj.write(json.dumps(_serialize_to_jspf(playlist,
                                                             track_count=track_count,
                                                             algorithm_metadata=algorithm_metadata)))

    def submit(self, token, created_for=None):
        """
            Submit the playlist to ListenBrainz.

            token - the ListenBrainz user token to use to submit this playlist.
            created_for - the ListenBrainz user name for whom this playlist was created.
                          the token above must be an Approved Playlist Bot in the ListenBrainz
                          server, otherwise the subission will fail.
        """

        if not self.playlists:
            raise PipelineError("Playlists have not been generated yet.")

        playlist_mbids = []
        for playlist in self.playlists:
            print("submit %d tracks" % len(playlist.recordings))
            if len(playlist.recordings) == 0:
                print("skip submitting a zero length playlist.")
                continue

            r = requests.post(LISTENBRAINZ_PLAYLIST_CREATE_URL,
                              json=_serialize_to_jspf(playlist, created_for),
                              headers={"Authorization": "Token " + str(token)})
            if r.status_code != 200:
                try:
                    err = r.json()["error"]
                except json.decoder.JSONDecodeError:
                    err = r.text

                raise PipelineError("Cannot post playlist to ListenBrainz: HTTP code %d: %s" %
                                    (r.status_code, err))

            try:
                result = json.loads(r.text)
            except ValueError as err:
                raise PipelineError("Cannot post playlist to ListenBrainz: " + str(err))

            playlist_mbids.append((LISTENBRAINZ_SERVER_URL + "/playlist/" + result["playlist_mbid"], result["playlist_mbid"]))

        return playlist_mbids


class PlaylistRedundancyReducerElement(Element):
    '''
        This element takes a larger playlist and whittles it down to a smaller playlist by
        removing some tracks in order to reduce the number of times a single artist appears
        in the playlist.
    '''

    def __init__(self, artist_count=15, max_num_recordings=50):
        super().__init__()
        self.artist_count = artist_count
        self.max_num_recordings = max_num_recordings

    @staticmethod
    def inputs():
        return [Playlist]

    @staticmethod
    def outputs():
        return [Playlist]

    def read(self, inputs):

        for playlist in inputs[0]:
            artists = defaultdict(int)
            for r in playlist.recordings:
                artists[r.artist.name] += 1

            self.debug("found %d artists" % len(artists.keys()))
            if len(artists.keys()) > self.artist_count:
                self.debug("playlist shaper fixing up playlist")
                filtered = []
                artists = defaultdict(int)
                for r in playlist.recordings:
                    if artists[r.artist.name] < 2: 
                        filtered.append(r)
                        artists[r.artist.name] += 1

                playlist.recordings = filtered[:self.max_num_recordings]
                break
            else:
                self.debug("playlist shaper returned full playlist")
                playlist.recordings = playlist.recordings[:self.max_num_recordings]

        return inputs[0]


class PlaylistShuffleElement(Element):
    '''
        Take in a list of playlists, pass on shuffled playlists.
    '''

    def __init__(self):
        super().__init__()

    @staticmethod
    def inputs():
        return [Playlist]

    @staticmethod
    def outputs():
        return [Playlist]

    def read(self, inputs):

        for playlist in inputs[0]:
            assert type(playlist) == Playlist
            playlist.shuffle()

        return inputs[0]


class PlaylistBPMSawtoothSortElement(Element):
    '''
        Sort a playlist by BPM going from slow to fast and back to slow.
    '''

    def __init__(self):
        super().__init__()

    @staticmethod
    def inputs():
        return [Playlist]

    @staticmethod
    def outputs():
        return [Playlist]

    def bpm_sawtooth_sort(self, recordings):
        try:
            sorted_recs = sorted(recordings, key=lambda rec: rec.acousticbrainz["bpm"])
        except AttributeError:
            raise RuntimeError("acousticbrainz.bpm not set for recording in playlist PBM sort.")

        # Sort the recordings by BPM ASC. Then, walking from the back of the array to the front,
        # Move every second track to the back of the array, creating a sawtooth shape of BPMs
        index = sorted_recs.index(max(sorted_recs, key=lambda rec: rec.acousticbrainz["bpm"]))
        while index >= 0:
            sorted_recs.append(sorted_recs.pop(index))
            index -= 2

        return sorted_recs


    def read(self, inputs):
        for playlist in inputs[0]:
            playlist.recordings = self.bpm_sawtooth_sort(playlist.recordings)

        return inputs[0]


class PlaylistMakerElement(Element):
    '''
        This element takes in Recordings and spits out a Playlist.
    '''

    def __init__(self, name, desc, patch_slug=None, user_name=None, max_num_recordings=None):
        super().__init__()
        self.name = name
        self.desc = desc
        self.patch_slug = patch_slug
        self.user_name = user_name
        self.max_num_recordings = max_num_recordings

    @staticmethod
    def inputs():
        return [Recording]

    @staticmethod
    def outputs():
        return [Playlist]

    def read(self, inputs):
        if self.max_num_recordings is not None:
            return [Playlist(name=self.name,
                    description=self.desc,
                    recordings=inputs[0][:self.max_num_recordings],
                    patch_slug=self.patch_slug,
                    user_name=self.user_name)]
        else:
            return [Playlist(name=self.name,
                    description=self.desc,
                    recordings=inputs[0],
                    patch_slug=self.patch_slug,
                    user_name=self.user_name)]

