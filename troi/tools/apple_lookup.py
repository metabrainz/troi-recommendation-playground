from .utils import create_http_session
import requests

APPLE_MUSIC_URL = f"https://api.music.apple.com/"
APPLE_MUSIC_IDS_LOOKUP_URL = "https://labs.api.listenbrainz.org/apple-music-id-from-mbid/json"

# def lookup_apple_music_ids(recordings):
#     """ Given a list of Recording elements, try to find spotify track ids from labs api spotify lookup using mbids
#     and add those to the recordings. """
#     response = requests.post(
#         APPLE_MUSIC_IDS_LOOKUP_URL,
#         json=[{"recording_mbid": recording.mbid} for recording in recordings]
#     )
#     response.raise_for_status()
#     apple_data = response.json()

#     mbid_apple_ids_index = {}
#     apple_id_mbid_index = {}
#     for recording, lookup in zip(recordings, apple_data):
#         if len(lookup["apple_music_track_ids"]) > 0:
#             recording.spotify_id = lookup["spotify_track_ids"][0]
#             mbid_spotify_ids_index[recording.mbid] = lookup["spotify_track_ids"]
#             for spotify_id in lookup["spotify_track_ids"]:
#                 spotify_id_mbid_index[spotify_id] = recording.mbid
#     return recordings, mbid_spotify_ids_index, spotify_id_mbid_index

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

# def submit_to_apple_music(playlist, apple_user_id: str, isPublic: bool = True, existing_url: str = None):
#     """ Submit or update an existing Apple Music playlist.

#     If existing urls are specified then isPublic arguments are ignored.
#     """
#     filtered_recordings = [recording for recording in playlist.recordings if recording.mbid]

#     _, mbid_apple_index, spotify_apple_index = lookup_apple_music_ids(filtered_recordings)
#     apple_music_track_ids = [recording.spotify_id for recording in filtered_recordings if recording.]
#     if len(spotify_track_ids) == 0:
#         return None, None

#     logger.info("submit %d tracks" % len(spotify_track_ids))

#     playlist_id, playlist_url = None, None
#     if existing_url:
#         # update existing playlist
#         playlist_url = existing_url
#         playlist_id = existing_url.split("/")[-1]
#         try:
#             spotify.playlist_change_details(playlist_id=playlist_id, name=playlist.name, description=playlist.description)
#         except SpotifyException as err:
#             # one possibility is that the user has deleted the spotify from playlist, so try creating a new one
#             logger.info("provided playlist url has been unfollowed/deleted by the user, creating a new one")
#             playlist_id, playlist_url = None, None

#     if not playlist_id:
#         # create new playlist
#         spotify_playlist = spotify.user_playlist_create(
#             user=spotify_user_id,
#             name=playlist.name,
#             public=is_public,
#             collaborative=is_collaborative,
#             description=playlist.description
#         )
#         playlist_id = spotify_playlist["id"]
#         playlist_url = spotify_playlist["external_urls"]["spotify"]
#     else:
#         # existing playlist, clear it
#         spotify.playlist_replace_items(playlist_id, [])

#     # spotify API allows a max of 100 tracks in 1 request
#     for chunk in chunked(spotify_track_ids, 100):
#         spotify.playlist_add_items(playlist_id, chunk)

#     fixup_spotify_playlist(spotify, playlist_id, mbid_spotify_index, spotify_mbid_index)

#     playlist.add_metadata({"external_urls": {"spotify": playlist_url}})

#     return playlist_url, playlist_id