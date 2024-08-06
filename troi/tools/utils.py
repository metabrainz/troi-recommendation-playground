import requests
import json
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

SOUNDCLOUD_URL = f"https://api.soundcloud.com/"

class SoundCloudException(Exception):
    def __init__(self, code, msg):
        self.code = code
        self.msg = msg
        super().__init__(f"http error {code}: {msg}")

class SoundcloudAPI:
    def __init__(self, access_token):
        self.access_token = access_token
        self.headers = {
            "Authorization": f"OAuth {self.access_token}",
            "Content-Type": "application/json"
        }
        self.session = self._create_http_session()

    def _create_http_session():
        """ Create an HTTP session with retry strategy for handling rate limits and server errors.
        """
        retry_strategy = Retry(
            total=3,
            status_forcelist=[429, 500, 502, 503, 504], 
            allowed_methods=["HEAD", "GET", "OPTIONS"], 
            backoff_factor=1
        )

        adapter = HTTPAdapter(max_retries=retry_strategy)
        http = requests.Session()
        http.mount("https://", adapter)
        http.mount("http://", adapter)
        return http

    def create_playlist(self, title, sharing="public" ,track_ids=None, description=None):
        url = f"{SOUNDCLOUD_URL}/playlists"
        data = {
            "playlist": {
                "title": title,
                "sharing": sharing
            }
        }
        if description:
            data["playlist"]["description"] = description
        response = self.session.post(url, headers=self.headers, data=json.dumps(data))
        return response.json()

    def add_playlist_tracks(self, playlist_id, track_ids):
        url = f"{SOUNDCLOUD_URL}/playlists/{playlist_id}"
        data = {
            "playlist": {
                "tracks": [{"id": track_id} for track_id in track_ids]
            }
        }
        response = self.session.put(url, headers=self.headers, data=json.dumps(data))
        return response.json()

    def update_playlist_details(self, playlist_id, title=None, description=None):
        url = f"{self.base_url}/playlists/{playlist_id}"
        data = {
            "playlist": {}
        }
        if title:
            data["playlist"]["title"] = title
        if description:
            data["playlist"]["description"] = description

        response = self.session.put(url, headers=self.headers, data=json.dumps(data))
        return response.json()
    
    def get_tracks(self, track_ids):
        track_details = []
        for track_id in track_ids:
            url = f"{SOUNDCLOUD_URL}/tracks/{track_id}"
            response = self.session.get(url, headers=self.headers)
            if response.status_code == 200:
                track = response.json()
                track_details.append({
                    "id": track["id"],
                    "title": track["title"],
                    "playable": track.get("streamable", True)
                })
            else:
                track_details.append({
                    "id": track_id,
                    "title": None,
                    "playable": False
                })
        return track_details

    def get_playlist_tracks(self, playlist_id):
        url = f"{SOUNDCLOUD_URL}/playlists/{playlist_id}/tracks"
        response = self.session.get(url, headers=self.headers)
        response.raise_for_status()
        
        response = response.json()
        return response

    def get_unplayable_tracks(self, playlist_id):
        url = f"{SOUNDCLOUD_URL}/playlists/{playlist_id}/tracks"
        response = self.session.get(url, headers=self.headers)
        response.raise_for_status()

        tracks = response.json().get("tracks", [])
        unplayable_tracks = [track for track in tracks if not track.get("streamable", True)]
        return unplayable_tracks
