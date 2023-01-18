from collections import defaultdict
import json
from typing import Dict, Tuple


import requests
import spotipy
from spotipy import SpotifyException

from troi import Recording, Playlist, PipelineError, Element, Artist, Release
from troi.operations import is_homogeneous
from troi.print_recording import PrintRecordingList
from troi.tools.spotify_lookup import lookup_spotify_ids, fixup_spotify_playlist

LISTENBRAINZ_SERVER_URL = "https://listenbrainz.org"
LISTENBRAINZ_API_URL = "https://api.listenbrainz.org"
LISTENBRAINZ_PLAYLIST_FETCH_URL = LISTENBRAINZ_API_URL + "/1/playlist/"
LISTENBRAINZ_PLAYLIST_CREATE_URL = LISTENBRAINZ_API_URL + "/1/playlist/create"
PLAYLIST_TRACK_URI_PREFIX = "https://musicbrainz.org/recording/"
PLAYLIST_ARTIST_URI_PREFIX = "https://musicbrainz.org/artist/"
PLAYLIST_RELEASE_URI_PREFIX = "https://musicbrainz.org/release/"
PLAYLIST_URI_PREFIX = "https://listenbrainz.org/playlist/"
PLAYLIST_EXTENSION_URI = "https://musicbrainz.org/doc/jspf#playlist"
PLAYLIST_TRACK_EXTENSION_URI = "https://musicbrainz.org/doc/jspf#track"


def _serialize_to_jspf(playlist, created_for=None, track_count=None):
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
        # TODO: This element is in the wrong location!
        data["created_for"] = created_for

    if playlist.additional_metadata:
        data["extension"][PLAYLIST_EXTENSION_URI]["additional_metadata"] = playlist.additional_metadata

    if not track_count or track_count < 0 or track_count > len(playlist.recordings):
        track_count = len(playlist.recordings)

    tracks = []
    for e in playlist.recordings[:track_count]:
        track = {}
        artist_mbids = []
        if e.artist is not None:
            artist_mbids = [ str(mbid) for mbid in e.artist.mbids or [] ]
            track["creator"] = e.artist.name if e.artist else ""

        track["album"] = e.release.name if e.release else ""
        track["title"] = e.name
        track["identifier"] = "https://musicbrainz.org/recording/" + str(e.mbid)
        if artist_mbids:
            track["extension"] = {
                PLAYLIST_TRACK_EXTENSION_URI: {
                    "artist_identifiers": artist_mbids,
                }
            }
        tracks.append(track)

    data['track'] = tracks

    return { "playlist" : data }


def _deserialize_from_jspf(data) -> Playlist:
    """ Deserialize a ListenBrainz JSPF playlist to a Playlist entity. """
    data = data["playlist"]
    recordings = []

    for track in data["track"]:
        recording = Recording(name=track["title"], mbid=track["identifier"].split("/")[-1])
        if track.get("creator"):
            artist = Artist(name=track["creator"])
            extension = track["extension"][PLAYLIST_TRACK_EXTENSION_URI]
            if extension.get("artist_identifiers"):
                artist_mbids = [url.split("/")[-1] for url in extension.get("artist_identifiers")]
                artist.mbids = artist_mbids
            recording.artist = artist

        if track.get("album"):
            recording.release = Release(name=track["album"])

        recordings.append(recording)

    playlist = Playlist(
        name=data["title"],
        description=data.get("annotation"),
        mbid=data["identifier"].split("/")[-1],
        recordings=recordings
    )
    return playlist


class PlaylistElement(Element):
    """
        Take a list of Recordings or Playlists and save, print or submit them. The playlist element takes
        lists of recordings or lists of playlists and saves them to disk or submits them to ListenBrainz.

        This element can receive a list of recordings in which case that will be treated as a single
        playlist. This element can also recevied a list of playlists, in which case each playlist will
        be saved/submitted individually.

        Note that the Playlist entity object is distinct from this class -- the Playlist object tracks
        the core components of a playlist for passing through troi piplines, whereas this clas
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

    def save(self, track_count=None, file_obj=None):
        """Save each playlist to disk, giving each playlist a unique name if none was provided.

           Arguments:
              track_count: If provided, write out only this many tracks to the playlist
              file_obj: If provided, write the JSPF file to this file_object
        """

        if not self.playlists:
            raise PipelineError("Playlists have not been generated yet.")

        for i, playlist in enumerate(self.playlists):
            if not file_obj:
                filename = playlist.filename or "playlist_%03d.jspf" % i
                with open(filename, "w") as f:
                    f.write(json.dumps(_serialize_to_jspf(playlist, track_count=track_count)))
            else:
                file_obj.write(json.dumps(_serialize_to_jspf(playlist, track_count=track_count)))

    def submit(self, token, created_for=None):
        """
            Submit the playlist to ListenBrainz.

            :param token: the ListenBrainz user token to use to submit this playlist.
            :param created_for: the ListenBrainz user name for whom this playlist was created. the token above must be an Approved Playlist Bot in the ListenBrainz server, otherwise the subission will fail.
        """

        if not self.playlists:
            raise PipelineError("Playlists have not been generated yet.")

        playlist_mbids = []
        for playlist in self.playlists:
            if len(playlist.recordings) == 0:
                continue

            print("submit %d tracks" % len(playlist.recordings))
            if playlist.patch_slug is not None:
                playlist.add_metadata({"algorithm_metadata": {"source_patch": playlist.patch_slug}})
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

            playlist.mbid = result["playlist_mbid"]
            playlist_mbids.append((LISTENBRAINZ_SERVER_URL + "/playlist/" + result["playlist_mbid"], result["playlist_mbid"]))

        return playlist_mbids

    def submit_to_spotify(self, user_id: str, token: str, is_public: bool = True, is_collaborative: bool = False,
                          existing_urls: str = None):
        """ Given spotify user id, spotify auth token with appropriate permissions and playlist visibility
         characteristics, upload the playlists generated in the current element to Spotify and return the
         urls of submitted playlists.

        If existing urls are specified then is_public and is_collaborative arguments are ignored.
        """
        sp = spotipy.Spotify(auth=token)
        submitted = []

        for idx, playlist in enumerate(self.playlists):

            if len(playlist.recordings) == 0:
                continue
            filtered_recordings = [r for r in playlist.recordings if r.mbid]

            _, mbid_spotify_index, spotify_mbid_index = lookup_spotify_ids(filtered_recordings)
            spotify_track_ids = [r.spotify_id for r in filtered_recordings if r.spotify_id]
            if len(spotify_track_ids) == 0:
                continue

            print("submit %d tracks" % len(spotify_track_ids))

            playlist_id, playlist_url = None, None
            if existing_urls and idx < len(existing_urls) and existing_urls[idx]:
                # update existing playlist
                playlist_url = existing_urls[idx]
                playlist_id = playlist_url.split("/")[-1]
                try:
                    sp.playlist_change_details(
                        playlist_id=playlist_id,
                        name=playlist.name,
                        description=playlist.description
                    )
                except SpotifyException as err:
                    # one possibility is that the user has deleted the spotify from playlist, so try creating a new one
                    print("provided playlist url has been unfollowed/deleted by the user, creating a new one")
                    playlist_id, playlist_url = None, None

            if not playlist_id:
                # create new playlist
                spotify_playlist = sp.user_playlist_create(
                    user=user_id,
                    name=playlist.name,
                    public=is_public,
                    collaborative=is_collaborative,
                    description=playlist.description
                )
                playlist_id = spotify_playlist["id"]
                playlist_url = spotify_playlist["external_urls"]["spotify"]

            result = sp.playlist_replace_items(playlist_id, spotify_track_ids)
            fixup_spotify_playlist(sp, playlist_id, mbid_spotify_index, spotify_mbid_index)
            submitted.append((playlist_url, playlist_id))

            playlist.add_metadata({"external_urls": {"spotify": playlist_url}})

        return submitted


class PlaylistRedundancyReducerElement(Element):
    '''
        This element takes a larger playlist and whittles it down to a smaller playlist by
        removing some tracks in order to reduce the number of times a single artist appears
        in the playlist.
    '''

    def __init__(self, max_artist_occurrence=2, max_num_recordings=50):
        super().__init__()
        self.max_num_recordings = max_num_recordings
        self.max_artist_occurrence = max_artist_occurrence

    @staticmethod
    def inputs():
        return [Playlist]

    @staticmethod
    def outputs():
        return [Playlist]

    def read(self, inputs):

        playlists = []

        for playlist in inputs[0]:
            kept = []
            artists = defaultdict(int)
            for r in playlist.recordings:
                keep = True
                for mbid in r.artist.mbids:
                    if artists[mbid] >= self.max_artist_occurrence:
                        keep = False
                        break
                    artists[mbid] += 1

                if keep:
                    kept.append(r)

            playlist.recordings = kept[:self.max_num_recordings]

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


class PlaylistFromJSPFElement(Element):
    """ Create a troi.Playlist entity from a ListenBrainz JSPF playlist """

    def __init__(self, playlist_mbid, token=None):
        """
            Args:
                playlist_mbid: mbid of the ListenBrainz playlist to be used for creating the playlist element
                token: the listenbrainz auth token to fetch the playlist, only needed for private playlists
        """
        super().__init__()
        self.playlist_mbid = playlist_mbid
        self.token = token

    @staticmethod
    def outputs():
        return [Playlist]

    def read(self, inputs):
        headers = None
        if self.token:
            headers = {"Authorization": f"Token {self.token}"}
        response = requests.get(LISTENBRAINZ_PLAYLIST_FETCH_URL + self.playlist_mbid, headers=headers)
        response.raise_for_status()
        data = response.json()
        return [_deserialize_from_jspf(data)]


class DumpElement(Element):
    """
        Accept whatever and print it out in a reasonably sane manner.
    """

    def __init__(self):
        super().__init__()

    @staticmethod
    def inputs():
        return [Recording, Playlist]

    @staticmethod
    def outputs():
        return [Recording, Playlist]

    def read(self, inputs):
        for input in inputs:
            pr = PrintRecordingList()
            pr.print(input)

        return inputs[0]

