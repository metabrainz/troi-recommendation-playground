import requests

SOUNDCLOUD_URL = f"https://api.soundcloud.com/"

def convert_soundcloud_tracks_to_json(soundcloud_tracks):
    tracks= []
    for track in soundcloud_tracks:
        tracks.append({
            "recording_name": track['attributes']['name'],
            "artist_name": track['attributes']['artistName'],
        })
    return tracks


def get_tracks_from_soundcloud_playlist(developer_token, playlist_id):
    """ Get tracks from the Apple Music playlist.
    """
    headers = {
        "Authorization": f"Bearer {developer_token}",
    }
    response = requests.get(SOUNDCLOUD_URL+f"/playlists/{playlist_id}", headers=headers)
    if response.status_code == 200:
        print("got in")
        response = response.json()
        tracks = response["tracks"]
        name = response["title"]
        description = response["description"]
    else:
        response.raise_for_status()

    mapped_tracks= []
    for track in tracks:
        artist, song = track['title'].split(" - ")
        mapped_tracks.append({
            "recording_name": song,
            "artist_name": artist,
        })
    
    print(mapped_tracks)
    return mapped_tracks, name, description


# get_tracks_from_soundcloud_playlist("2-294758-355389761-ipvsDC07nvDHUa", 384588551)