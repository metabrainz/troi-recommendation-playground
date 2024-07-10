import requests

SOUNDCLOUD_URL = f"https://api.soundcloud.com/"

def get_tracks_from_soundcloud_playlist(developer_token, playlist_id):
    """ Get tracks from the Apple Music playlist.
    """
    headers = {
        "Authorization": f"Bearer {developer_token}",
    }
    response = requests.get(SOUNDCLOUD_URL+f"/playlists/{playlist_id}", headers=headers)
    if response.status_code == 200:
        response = response.json()
        tracks = response["tracks"]
        name = response["title"]
        description = response["description"]
    else:
        response.raise_for_status()

    mapped_tracks = [
        {
            "recording_name": track['title'].split(" - ")[1] if " - " in track['title'] else track['title'],
            "artist_name": track['title'].split(" - ")[0] if " - " in track['title'] else track['user']['username']
        }
        for track in tracks
    ]

    return mapped_tracks, name, description
