import logging
from collections import defaultdict
import json
from time import sleep


import requests
import spotipy
from troi.tools.utils import AppleMusicAPI

from troi import Recording, Playlist, PipelineError, Element, Artist, ArtistCredit, Release
from troi.operations import is_homogeneous
from troi.print_recording import PrintRecordingList
from troi.tools.common_lookup import music_service_tracks_to_mbid
from troi.tools.spotify_lookup import submit_to_spotify
from troi.tools.apple_lookup import submit_to_apple_music
from troi.tools.soundcloud_lookup import submit_to_soundcloud
from troi.tools.utils import SoundcloudAPI

logger = logging.getLogger(__name__)

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
SUBSONIC_URI_PREFIX = "https://subsonic.org/entity/song/"


def _serialize_to_jspf(playlist, created_for=None, track_count=None):
    """
        Serialize a playlist to JSPF.

        Arguments:
            created_for: The user name of the user for whom this playlist
                         was created.
            track_count: The number of tracks to serialize. If not provided,
                         all tracks will be serialized.
    """

    data = {"creator": "ListenBrainz Troi", "extension": {PLAYLIST_EXTENSION_URI: {"public": True}}}

    if playlist.name:
        data["title"] = playlist.name

    if playlist.description:
        data["annotation"] = playlist.description

    if created_for:
        data["extension"][PLAYLIST_EXTENSION_URI]["created_for"] = created_for

    if playlist.additional_metadata:
        data["extension"][PLAYLIST_EXTENSION_URI]["additional_metadata"] = playlist.additional_metadata

    if not track_count or track_count < 0 or track_count > len(playlist.recordings):
        track_count = len(playlist.recordings)

    tracks = []
    for e in playlist.recordings[:track_count]:
        track = {}
        artist_mbids = []
        if e.artist_credit is not None:
            artist_mbids = [str(artist.mbid) for artist in e.artist_credit.artists or []]
            track["creator"] = e.artist_credit.name if e.artist_credit else ""

        track["title"] = e.name
        track["identifier"] = ["https://musicbrainz.org/recording/" + str(e.mbid)]

        loc = e.musicbrainz.get("filename", None)
        if loc is not None:
            track["location"] = loc

        if e.duration is not None:
            track["duration"] = e.duration

        if artist_mbids:
            track["extension"] = {
                PLAYLIST_TRACK_EXTENSION_URI: {
                    "artist_identifiers": artist_mbids,
                }
            }

        if e.release is not None:
            if e.release.name is not None and e.release.name != "":
                track["album"] = e.release.name

            if e.release.mbid is not None and e.release.mbid != "":
                track["extension"][PLAYLIST_TRACK_EXTENSION_URI]["release_identifier"] = \
                      PLAYLIST_RELEASE_URI_PREFIX + e.release.mbid

        # Output subsonic_ids to the playlist
        subsonic_id = e.musicbrainz.get("subsonic_id", None)
        if subsonic_id is not None:
            if "additional_metadata" not in track["extension"][PLAYLIST_TRACK_EXTENSION_URI]:
                track["extension"][PLAYLIST_TRACK_EXTENSION_URI]["additional_metadata"] = {}
            track["extension"][PLAYLIST_TRACK_EXTENSION_URI]["additional_metadata"]["subsonic_identifier"] = \
                  SUBSONIC_URI_PREFIX + subsonic_id

        tracks.append(track)

    data['track'] = tracks

    return {"playlist": data}


def _deserialize_from_jspf(data) -> Playlist:
    """ Deserialize a ListenBrainz JSPF playlist to a Playlist entity. """
    data = data["playlist"]
    recordings = []

    for track in data["track"]:
        identifiers = track["identifier"]
        if isinstance(identifiers, str):
            identifiers = [identifiers]

        mbid = None
        for identifier in identifiers:
            if identifier.startswith("https://musicbrainz.org/recording/") or \
                    identifier.startswith("http://musicbrainz.org/recording/"):
                mbid = identifier.split("/")[-1]
                break

        recording = Recording(name=track["title"], mbid=mbid)
        if track.get("creator"):
            extension = track["extension"][PLAYLIST_TRACK_EXTENSION_URI]
            if extension.get("artist_identifiers"):
                artist_mbids = [url.split("/")[-1] for url in extension.get("artist_identifiers")]
                artists = [Artist(mbid=mbid) for mbid in artist_mbids]
            else:
                artists = None
            recording.artist_credit = ArtistCredit(name=track["creator"], artists=artists)

        if track.get("album"):
            recording.release = Release(name=track["album"])

        musicbrainz = {}
        if track.get("location"):
            musicbrainz["filename"] = track.get("location")

        try:
            musicbrainz["subsonic_id"] = track["extension"][PLAYLIST_TRACK_EXTENSION_URI] \
                                              ["additional_metadata"]["subsonic_identifier"]
            musicbrainz["subsonic_id"] = musicbrainz["subsonic_id"][len(SUBSONIC_URI_PREFIX):]
        except KeyError:
            pass

        recording.musicbrainz = musicbrainz
        recordings.append(recording)

    try:
        ident = data["identifier"].split("/")[-1],
    except KeyError:
        ident = ""
    playlist = Playlist(name=data["title"],
                        description=data.get("annotation"),
                        mbid=ident,
                        recordings=recordings)
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
                logger.info("No recordings or playlists generated to save.")
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
            logger.error("[no playlist(s) generated yet]")
            return

        for i, playlist in enumerate(self.playlists):
            if playlist.name:
                logger.info("playlist: '%s'" % playlist.name)
            else:
                logger.info("playlist: %d" % i)

            for recording in playlist.recordings:
                if not recording:
                    logger.info("[invalid Recording]")
                    continue
                self.print_recording.print(recording)

            if playlist.description:
                logger.info("description: '%s'" % playlist.description)

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

    def get_jspf(self, playlist_index=0):
        """Get the JSPF for the playlist at the given playlist index. Defaults to index 0."""

        try:
            return _serialize_to_jspf(self.playlists[playlist_index])
        except IndexError:
            return None

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

            logger.info("submit %d tracks" % len(playlist.recordings))
            if playlist.patch_slug is not None:
                playlist.add_metadata({"algorithm_metadata": {"source_patch": playlist.patch_slug}})

            while True:
                r = requests.post(LISTENBRAINZ_PLAYLIST_CREATE_URL,
                                  json=_serialize_to_jspf(playlist, created_for),
                                  headers={"Authorization": "Token " + str(token)})
                if r.status_code == 429:
                    sleep(2)
                    continue

                if r.status_code != 200:
                    try:
                        err = r.json()["error"]
                    except json.decoder.JSONDecodeError:
                        err = r.text

                    raise PipelineError("Cannot post playlist to ListenBrainz: HTTP code %d: %s" % (r.status_code, err))

                break

            try:
                result = json.loads(r.text)
            except ValueError as err:
                raise PipelineError("Cannot post playlist to ListenBrainz: " + str(err))

            playlist.mbid = result["playlist_mbid"]
            playlist_mbids.append((LISTENBRAINZ_SERVER_URL + "/playlist/" + result["playlist_mbid"], result["playlist_mbid"]))

        return playlist_mbids

    def submit_to_spotify(self,
                          user_id: str,
                          token: str,
                          is_public: bool = True,
                          is_collaborative: bool = False,
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

            existing_url = None
            if existing_urls and idx < len(existing_urls) and existing_urls[idx]:
                existing_url = existing_urls[idx]

            playlist_url, playlist_id = submit_to_spotify(sp, playlist, user_id, is_public, is_collaborative, existing_url)
            submitted.append((playlist_url, playlist_id))

        return submitted

    def submit_to_apple_music(self,
                          user_token: str,
                          developer_token: str,
                          is_public: bool = True,
                          existing_urls: str = None):
        """ Given apple music user token, developer token, upload the playlists generated in the current element to Apple Music and return the
        urls of submitted playlists.

        """
        apple = AppleMusicAPI(developer_token, user_token)
        submitted = []
        for idx, playlist in enumerate(self.playlists):
            if len(playlist.recordings) == 0:
                continue

            existing_url = None
            if existing_urls and idx < len(existing_urls) and existing_urls[idx]:
                existing_url = existing_urls[idx]

            playlist_url, playlist_id = submit_to_apple_music(apple, playlist, is_public, existing_url)
            submitted.append((playlist_url, playlist_id))

        return submitted

    def submit_to_soundcloud(self,
                             access_token: str,
                             is_public: bool = True,
                             existing_urls: str = None):
        """ Given soundcloud user id, soundcloud auth token, upload the playlists generated in the current element to Soundcloud and return the
        urls of submitted playlists.

        """
        sd = SoundcloudAPI(access_token=access_token)
        submitted = []

        for idx, playlist in enumerate(self.playlists):
            if len(playlist.recordings) == 0:
                continue

            existing_url = None
            if existing_urls and idx < len(existing_urls) and existing_urls[idx]:
                existing_url = existing_urls[idx]

            playlist_url, playlist_id = submit_to_soundcloud(sd, playlist, is_public, existing_url)
            submitted.append((playlist_url, playlist_id))

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

        :param name: The name of the playlist
        :param desc: The description of the playlist
        :param patch-slug: The patch slug (URL-safe short name) of the patch that created the playlist. Optional.
        :param max_num_recordings: The maximum number of recordings to have in the playlist. Extras are discarded. Optional argument, and the default is to keep all recordings
        :param max_artist_occurrence: The number of times and artist is allowed to appear in the playlist. Any recordings that exceed this count ared discarded. Optional, default is to keep all recordings.
        :param shuffle: If True, the playlist will be shuffled before being truncated. Optional. Default: False
        :param is_april_first: If True, do something very sneaky. Default: False.
    '''

    def __init__(self,
                 name=None,
                 desc=None,
                 patch_slug=None,
                 user_name=None,
                 max_num_recordings=None,
                 max_artist_occurrence=None,
                 shuffle=False,
                 expires_at=None,
                 is_april_first=False):
        super().__init__()
        self.name = name
        self.desc = desc
        self.patch_slug = patch_slug
        self.user_name = user_name
        self.max_num_recordings = max_num_recordings
        self.max_artist_occurrence = max_artist_occurrence
        self.shuffle = shuffle
        self.expires_at = expires_at
        self.is_april_first = is_april_first

    @staticmethod
    def inputs():
        return [Recording]

    @staticmethod
    def outputs():
        # We never actually return more than one playlist.
        return [Playlist]

    def read(self, inputs):
        recordings = inputs[0]

        if self.max_num_recordings is None:
            max_num_recordings = len(recordings)
        else:
            max_num_recordings = self.max_num_recordings

        if self.max_artist_occurrence is not None:
            kept = []
            artists = defaultdict(int)
            for r in recordings:
                keep = True
                for mbid in [ a.mbid for a in r.artist_credit.artists ]:
                    if artists[mbid] >= self.max_artist_occurrence:
                        keep = False
                        break
                    artists[mbid] += 1

                if keep:
                    kept.append(r)

            recordings = kept[:max_num_recordings]
        else:
            recordings = recordings[:max_num_recordings]

        # Call the patch's post_process function
        self.patch.post_process()

        if self.name is None:
            self.name = self.local_storage["_playlist_name"]

        if self.desc is None:
            self.desc = self.local_storage["_playlist_desc"]

        playlist = Playlist(name=self.name,
                            description=self.desc,
                            recordings=recordings,
                            patch_slug=self.patch_slug,
                            user_name=self.user_name)
        if self.shuffle:
            playlist.shuffle()

        if self.expires_at is not None:
            playlist.add_metadata({ "expires_at": self.expires_at.isoformat() })

        if self.is_april_first:
            try:
                playlist.recordings[2].mbid = "8f3471b5-7e6a-48da-86a9-c1c07a0f47ae"
            except IndexError:
                pass

        return [playlist]


class RecordingsFromMusicServiceElement(Element):
    """ Create a troi.Playlist entity from track and artist names."""

    def __init__(self, token=None, playlist_id=None, music_service=None, apple_user_token=None):
        """
            Args:
                playlist_id: id of the playlist to be used for creating the playlist element
                token: the Spotify token to fetch the playlist tracks
                music_service: the name of the music service to be used for fetching the playlist data
                apple_music_token (optional): the user token for Apple Music API 
        """
        super().__init__()
        self.token = token
        self.playlist_id = playlist_id
        self.music_service = music_service
        self.apple_user_token = apple_user_token


    @staticmethod
    def outputs():
        return [ Recording ]

    def read(self, inputs):
        recordings = []

        mbid_mapped_tracks = music_service_tracks_to_mbid(self.token, self.playlist_id, self.music_service, self.apple_user_token)
        if mbid_mapped_tracks:
            for mbid in mbid_mapped_tracks:
                recordings.append(Recording(mbid=mbid))

        return recordings

    
class PlaylistFromJSPFElement(Element):
    """ Create a troi.Playlist entity from a ListenBrainz JSPF playlist or LB playlist."""

    def __init__(self, playlist_mbid=None, jspf=None, token=None):
        """
            The caller must pass either playlist_mbid or the jspf itself, but not both.
            Args:
                playlist_mbid: mbid of the ListenBrainz playlist to be used for creating the playlist element
                jspf: The actual JSPF for the playlist.
                token: the listenbrainz auth token to fetch the playlist, only needed for private playlists
        """
        super().__init__()
        self.playlist_mbid = playlist_mbid
        self.token = token
        self.jspf = jspf

        if self.jspf is not None and self.playlist_mbid is not None:
            raise RuntimeError("Pass either jspf or playlist_mbid to PlaylistFromJSPFElement, not both.")

    @staticmethod
    def outputs():
        return [Playlist]

    def read(self, inputs):
        if self.playlist_mbid:
            headers = None
            if self.token:
                headers = {"Authorization": f"Token {self.token}"}
            response = requests.get(LISTENBRAINZ_PLAYLIST_FETCH_URL + self.playlist_mbid, headers=headers)
            response.raise_for_status()
            data = response.json()
            return [_deserialize_from_jspf(data)]
        else:
            return [_deserialize_from_jspf(self.jspf)]


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
