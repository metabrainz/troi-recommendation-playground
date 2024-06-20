import logging

import requests
from more_itertools import chunked

from troi.tools.apple_lookup import get_tracks_from_apple_playlist, convert_apple_tracks_to_json
from troi.tools.spotify_lookup import get_tracks_from_spotify_playlist, convert_spotify_tracks_to_json

MAX_LOOKUPS_PER_POST = 50
MBID_LOOKUP_URL = "https://api.listenbrainz.org/1/metadata/lookup/"

logger = logging.getLogger(__name__)


def music_service_tracks_to_mbid(token, playlist_id, music_service, apple_user_token=None):
    """ Convert Spotify playlist tracks to a list of MBID tracks.
    """
    if music_service == "spotify":
        tracks_from_playlist, name, desc = get_tracks_from_spotify_playlist(token, playlist_id)
        tracks = convert_spotify_tracks_to_json(tracks_from_playlist)
    elif music_service == "apple_music":
        tracks_from_playlist, name, desc = get_tracks_from_apple_playlist(token, apple_user_token, playlist_id)
        tracks = convert_apple_tracks_to_json(tracks_from_playlist)
    else:
        raise ValueError("Unknown music service")

    track_lists = list(chunked(tracks, MAX_LOOKUPS_PER_POST))
    return mbid_mapping_spotify(track_lists)


def mbid_mapping_spotify(track_lists):
    """ Given a track_name and artist_name, try to find MBID for these tracks from mbid lookup.
    """
    track_mbids = []
    for tracks in track_lists:
        params = {
            "recordings": tracks
        }
        response = requests.post(MBID_LOOKUP_URL, json=params)
        if response.status_code == 200:
            data = response.json()
            for d in data:
                if d is not None and "recording_mbid" in d:
                    track_mbids.append(d["recording_mbid"])
        else:
            logger.error("Error occurred: %s", response.text)
    return track_mbids
