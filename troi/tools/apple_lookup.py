import requests

from troi.tools.spotify_lookup import APPLE_MUSIC_URL


def convert_apple_tracks_to_json(apple_tracks):
    tracks= []
    for track in apple_tracks:
        tracks.append({
            "recording_name": track['attributes']['name'],
            "artist_name": track['attributes']['artistName'],
        })
    return tracks


def get_tracks_from_apple_playlist(developer_token, user_token, playlist_id):
    """ Get tracks from the Apple Music playlist.
    """
    headers = {
        "Authorization": f"Bearer {developer_token}",
        "Music-User-Token": user_token
    }
    response = requests.get(APPLE_MUSIC_URL+f"v1/me/library/playlists/{playlist_id}?include=tracks", headers=headers)
    if response.status_code == 200:
        response = response.json()
        tracks = response["data"][0]["relationships"]["tracks"]["data"]
        name = response["data"][0]["attributes"]["name"]
        description = response["data"][0]["attributes"]["description"]["standard"]
    else:
        response.raise_for_status()
    return tracks, name, description
