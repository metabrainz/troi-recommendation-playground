import logging
from collections import defaultdict
import re
import requests
import spotipy
from more_itertools import chunked
from spotipy import SpotifyException

logger = logging.getLogger(__name__)

APPLE_MUSIC_URL = f"https://api.music.apple.com/"
SPOTIFY_IDS_LOOKUP_URL = "https://labs.api.listenbrainz.org/spotify-id-from-mbid/json"
CLEAN_HTML_RE = re.compile('<.*?>')

def lookup_spotify_ids(recordings):
    """ Given a list of Recording elements, try to find spotify track ids from labs api spotify lookup using mbids
    and add those to the recordings. """
    response = requests.post(
        SPOTIFY_IDS_LOOKUP_URL,
        json=[{"recording_mbid": recording.mbid} for recording in recordings]
    )
    response.raise_for_status()
    spotify_data = response.json()
    mbid_spotify_ids_index = {}
    spotify_id_mbid_index = {}
    for recording, lookup in zip(recordings, spotify_data):
        if len(lookup["spotify_track_ids"]) > 0:
            recording.spotify_id = lookup["spotify_track_ids"][0]
            mbid_spotify_ids_index[recording.mbid] = lookup["spotify_track_ids"]
            for spotify_id in lookup["spotify_track_ids"]:
                spotify_id_mbid_index[spotify_id] = recording.mbid
    return recordings, mbid_spotify_ids_index, spotify_id_mbid_index


def _check_unplayable_tracks(sp: spotipy.Spotify, playlist_id: str):
    """ Retrieve tracks for given spotify playlist and split into lists of playable and unplayable tracks """
    playlist = sp.playlist_items(playlist_id, fields="items(track(name,id,is_playable))", market="from_token")
    playable = []
    unplayable = []
    for idx, item in enumerate(playlist["items"]):
        if item["track"]["is_playable"]:
            playable.append((idx, item["track"]["id"]))
        else:
            unplayable.append((idx, item["track"]["id"]))
    return playable, unplayable


def _get_alternative_track_ids(unplayable, mbid_spotify_id_idx, spotify_id_mbid_idx):
    """ For the list of unplayable track ids, find alternative tracks ids.

    mbid_spotify_id_idx is an index with mbid as key and list of equivalent spotify ids as value.
    spotify_id_mbid_idx is an index with spotify_id as key and the corresponding mbid as value.
    """
    index = defaultdict(list)
    spotify_ids = []
    
    for idx, spotify_id in unplayable:
        mbid = spotify_id_mbid_idx[spotify_id]
        other_spotify_ids = mbid_spotify_id_idx[mbid]

        for new_idx, new_spotify_id in enumerate(other_spotify_ids):
            if new_spotify_id == spotify_id:
                continue
            spotify_ids.append(new_spotify_id)
            index[idx].append(new_spotify_id)
            
    return spotify_ids, index


def _get_fixed_up_tracks(sp: spotipy.Spotify, spotify_ids, index):
    """ Lookup the all alternative spotify track ids, filter playable ones and if multiple track ids
        for same item match, prefer the one occurring earlier. If no alternative is playable, ignore the
        item altogether.
    """
    new_tracks = sp.tracks(spotify_ids, market="from_token")
    new_tracks_ids = set()
    for item in new_tracks["tracks"]:
        if item["is_playable"]:
            new_tracks_ids.add(item["id"])

    fixed_up_items = []
    for idx, spotify_ids in index.items():
        for spotify_id in spotify_ids:
            if spotify_id in new_tracks_ids:
                fixed_up_items.append((idx, spotify_id))
                break

    return fixed_up_items


def fixup_spotify_playlist(sp: spotipy.Spotify, playlist_id: str, mbid_spotify_id_idx, spotify_id_mbid_idx):
    """ Fix unplayable tracks in the given spotify playlist.

    Given a spotify playlist id, look it up and find unplayable tracks. If there are any unplayable tracks, try
    alternative spotify track ids from index/reverse_index if available. If alternative is not available or alternatives
    also are unplayable, remove the track entirely from the playlist. Finally, update the playlist if needed.
    """
    playable, unplayable = _check_unplayable_tracks(sp, playlist_id)
    if not unplayable:
        return

    alternative_ids, index = _get_alternative_track_ids(unplayable, mbid_spotify_id_idx, spotify_id_mbid_idx)
    if not alternative_ids:
        return

    fixed_up = _get_fixed_up_tracks(sp, alternative_ids, index)
    all_items = []
    all_items.extend(playable)
    all_items.extend(fixed_up)

    # sort all items by index value to ensure the order of tracks of original playlist is preserved
    all_items.sort(key=lambda x: x[0])
    # update all track ids the spotify playlist
    finalized_ids = [x[1] for x in all_items]

    # clear existing playlist
    sp.playlist_replace_items(playlist_id, [])
    # spotify API allows a max of 100 tracks in 1 request
    for chunk in chunked(finalized_ids, 100):
        sp.playlist_add_items(playlist_id, chunk)


def submit_to_spotify(spotify, playlist, spotify_user_id: str, is_public: bool = True,
                      is_collaborative: bool = False, existing_url: str = None):
    """ Submit or update an existing spotify playlist.

    If existing urls are specified then is_public and is_collaborative arguments are ignored.
    """
    filtered_recordings = [r for r in playlist.recordings if r.mbid]
    _, mbid_spotify_index, spotify_mbid_index = lookup_spotify_ids(filtered_recordings)
    spotify_track_ids = [r.spotify_id for r in filtered_recordings if r.spotify_id]
    if len(spotify_track_ids) == 0:
        return None, None

    logger.info("submit %d tracks" % len(spotify_track_ids))

    # Truncate to character limit for title
    playlist_name = playlist.name[0:100]
    # Remove HTML tags
    playlist_description = re.sub(
        CLEAN_HTML_RE, '', playlist.description or "")
    # Remove newlines
    playlist_description = ''.join(playlist_description.splitlines())
    # Truncate to character limit for description
    playlist_description = playlist_description[0:300]

    playlist_id, playlist_url = None, None
    if existing_url:
        # update existing playlist
        playlist_url = existing_url
        playlist_id = existing_url.split("/")[-1]
        try:
            spotify.playlist_change_details(
                playlist_id=playlist_id, name=playlist_name, description=playlist_description)
        except SpotifyException as err:
            # one possibility is that the user has deleted the spotify from playlist, so try creating a new one
            logger.info("provided playlist url has been unfollowed/deleted by the user, creating a new one")
            playlist_id, playlist_url = None, None

    if not playlist_id:
        # create new playlist
        spotify_playlist = spotify.user_playlist_create(
            user=spotify_user_id,
            name=playlist_name,
            public=is_public,
            collaborative=is_collaborative,
            description=playlist_description
        )
        playlist_id = spotify_playlist["id"]
        playlist_url = spotify_playlist["external_urls"]["spotify"]
    else:
        # existing playlist, clear it
        spotify.playlist_replace_items(playlist_id, [])

    # spotify API allows a max of 100 tracks in 1 request
    for chunk in chunked(spotify_track_ids, 100):
        spotify.playlist_add_items(playlist_id, chunk)

    fixup_spotify_playlist(spotify, playlist_id, mbid_spotify_index, spotify_mbid_index)

    playlist.add_metadata({"external_urls": {"spotify": playlist_url}})

    return playlist_url, playlist_id


def get_tracks_from_spotify_playlist(spotify_token, playlist_id):
    """ Get tracks from the Spotify playlist.
    """
    sp = spotipy.Spotify(auth=spotify_token, requests_timeout=10, retries=10)
    playlist_info = sp.playlist(playlist_id)

    offset = 0
    tracks = []

    # spotipy limits to 100 items for each call, so run iteratively with an offset until there are no more tracks
    while True:
        results = sp.playlist_items(playlist_id, limit=100, offset=offset)
        if len(results['items']) == 0:
            break

        tracks.extend(results['items'])
        # set new offset for the next loop
        offset = offset + len(results['items'])

    name = playlist_info["name"]
    description = playlist_info["description"]
    
    tracks = _convert_spotify_tracks_to_json(tracks)
    return tracks, name, description


def _convert_spotify_tracks_to_json(spotify_tracks: list):
    tracks = []
    for track in spotify_tracks:
        artists = track["track"].get("artists", [])
        artist_names = []
        for a in artists:
            name = a.get("name")
            if name is not None:
                artist_names.append(name)
        artist_name = ", ".join(artist_names)
        tracks.append({
            "recording_name": track["track"]["name"],
            "artist_name": artist_name,
        })
    return tracks
