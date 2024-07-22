from .utils import create_http_session

SOUNDCLOUD_URL = f"https://api.soundcloud.com/"

def get_tracks_from_soundcloud_playlist(developer_token, playlist_id):
    """ Get tracks from the Soundcloud playlist.
    """
    http = create_http_session()

    headers = {
        "Authorization": f"OAuth {developer_token}",
    }
    response = http.get(f"{SOUNDCLOUD_URL}/playlists/{playlist_id}", headers=headers)
    response.raise_for_status()

    response = response.json()
    tracks = response["tracks"]
    name = response["title"]
    description = response["description"]

    mapped_tracks = [
        {
            "recording_name": track['title'].split(" - ")[1] if " - " in track['title'] else track['title'],
            "artist_name": track['title'].split(" - ")[0] if " - " in track['title'] else track['user']['username']
        }
        for track in tracks
    ]

    return mapped_tracks, name, description
