import requests
import json
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


APPLE_MUSIC_URL = f"https://api.music.apple.com/v1/"

class AppleMusicException(Exception):
    def __init__(self, code, msg):
        self.code = code
        self.msg = msg
        super().__init__(f"Apple Music api error {code}: {msg}")

class AppleMusicAPI:
    def __init__(self, developer_token, user_token):
        self.developer_token = developer_token
        self.user_token = user_token
        self.headers = {
            "Authorization": f"Bearer {self.developer_token}",
            "Music-User-Token": self.user_token,
            "Content-Type": "application/json"
        }
    
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

    def create_playlist(self, name, description=None):
        url = f"{APPLE_MUSIC_URL}/me/library/playlists"
        data = {
            "attributes": {
                "name": name,
                "description": description
            }
        }
        
        response = requests.post(url, headers=self.headers, data=json.dumps(data))
        return response.json()

    def playlist_add_tracks(self, playlist_id, track_ids):
        url = f"{APPLE_MUSIC_URL}/me/library/playlists/{playlist_id}/tracks"
        data = {
            "data": [{"id": track_id, "type": "songs"} for track_id in track_ids]
        }

        response = requests.post(url, headers=self.headers, data=json.dumps(data))
        return response.json()

    # def replace_playlist_tracks(self, playlist_id, name=None, description=None):
    #     url = f"{self.base_url}/me/library/playlists/{playlist_id}"
    #     data = {
    #         "attributes": {}
    #     }
    #     if name:
    #         data["attributes"]["name"] = name
    #     if description:
    #         data["attributes"]["description"] = description

    #     response = requests.patch(url, headers=self.headers, data=json.dumps(data))
    #     return response.json()
    
    def get_playlist_tracks(self, playlist_id):
        with self._get_requests_session() as http:
            for _ in range(self.retries):
                url = f"{APPLE_MUSIC_URL}/me/library/playlists/{playlist_id}?include=tracks"
                response = http.get(url, headers=self.headers)
                response.raise_for_status()

                return response.json()
            response.raise_for_status()
    
    def get_unplayable_tracks(self, playlist_id):
        with self._get_requests_session() as http:
            for _ in range(self.retries):
                url = f"{APPLE_MUSIC_URL}/me/library/playlists/{playlist_id}/tracks"
                response = requests.get(url, headers=self.headers)
                response.raise_for_status()

                tracks = response.json().get("data", [])
                unplayable_tracks = [track for track in tracks if not track["attributes"].get("playParams")]
                return unplayable_tracks
            response.raise_for_status()
