import logging
import requests

from .utils import AppleMusicAPI, AppleMusicException
from more_itertools import chunked

logger = logging.getLogger(__name__)

APPLE_MUSIC_URL = f"https://api.music.apple.com/"
APPLE_MUSIC_IDS_LOOKUP_URL = "https://labs.api.listenbrainz.org/apple-music-id-from-mbid/json"

def lookup_apple_music_ids(recordings):
    """ Given a list of Recording elements, try to find Apple Music track ids from labs api apple_music_id lookup_from_mbid
    and add those to the recordings. """
    response = requests.post(
        APPLE_MUSIC_IDS_LOOKUP_URL,
        json=[{"recording_mbid": recording.mbid} for recording in recordings]
    )
    response.raise_for_status()
    apple_data = response.json()

    mbid_apple_music_ids_index = {}
    apple_id_mbid_index = {}
    for recording, lookup in zip(recordings, apple_data):
        if len(lookup["apple_music_track_ids"]) > 0:
            recording.apple_music_id = lookup["apple_music_track_ids"][0]
            mbid_apple_music_ids_index[recording.mbid] = lookup["apple_music_track_ids"]
            for apple_music_id in lookup["apple_music_track_ids"]:
                apple_id_mbid_index[apple_music_id] = recording.mbid
    return recordings, mbid_apple_music_ids_index, apple_id_mbid_index

def get_tracks_from_apple_playlist(developer_token, user_token, playlist_id):
    """ Get tracks from the Apple Music playlist.
    """
    apple = AppleMusicAPI(developer_token, user_token)
    tracks, name, description = apple.get_playlist_tracks(playlist_id)

    mapped_tracks = [
        {
            "recording_name": track['attributes']['name'],
            "artist_name": track['attributes']['artistName']
        }
        for track in tracks
    ]

    return mapped_tracks, name, description

def submit_to_apple_music(apple: AppleMusicAPI, playlist, is_public: bool=True, existing_url=None):
    """ Submit or update an existing Apple Music playlist.

    If existing urls are specified then isPublic arguments are ignored.
    """
    filtered_recordings = [recording for recording in playlist.recordings if recording.mbid]
    _, mbid_apple_music_index, apple_music_mbid_index = lookup_apple_music_ids(filtered_recordings)
    apple_music_track_ids = [recording.apple_music_id for recording in filtered_recordings if recording.apple_music_id]
    if len(apple_music_track_ids) == 0:
        return None, None

    logger.info("submit %d tracks" % len(apple_music_track_ids))

    playlist_id, playlist_url = None, None

    if existing_url:
        logger.info("Apple Music API does not support updating playlists, --apple-music-url paramenter will be ignored. Creating a new playlist...")

    if not playlist_id:
        # create new playlist
        apple_playlist = apple.create_playlist(
            name=playlist.name,
            description=playlist.description,
            is_public=is_public
        )
        playlist_id = apple_playlist["data"][0]["id"]
        playlist_url = apple_playlist["data"][0]["href"]

    for chunk in chunked(apple_music_track_ids, 100):
        apple.playlist_add_tracks(playlist_id, chunk)

    playlist.add_metadata({"external_urls": {"apple_music": playlist_url}})

    return playlist_url, playlist_id
