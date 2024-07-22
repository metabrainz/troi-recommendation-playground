import requests
from .utils import create_http_session

APPLE_MUSIC_URL = f"https://api.music.apple.com/"

def get_tracks_from_apple_playlist(developer_token, user_token, playlist_id):
    """ Get tracks from the Apple Music playlist.
    """
    http = create_http_session()

    headers = {
        "Authorization": f"Bearer {developer_token}",
        "Music-User-Token": user_token
    }
    response = http.get(APPLE_MUSIC_URL+f"v1/me/library/playlists/{playlist_id}?include=tracks", headers=headers)
    response.raise_for_status()

    response = response.json()
    tracks = response["data"][0]["relationships"]["tracks"]["data"]
    name = response["data"][0]["attributes"]["name"]
    description = response["data"][0]["attributes"].get("description", {}).get("standard", "")

    mapped_tracks = [
        {
            "recording_name": track['attributes']['name'],
            "artist_name": track['attributes']['artistName']
        }
        for track in tracks
    ]

    return mapped_tracks, name, description
