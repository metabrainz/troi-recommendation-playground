from math import fabs
import requests
import ujson
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials

from troi import Element, Artist, Recording, PipelineError
import config

        #{'danceability': 0.335, 'energy': 0.68, 'key': 0, 'loudness': -9.1, 'mode': 1, 'speechiness': 0.0343, 'acousticness': 0.153, 'instrumentalness': 0.00272, 'liveness': 0.222, 'valence': 0.377, 'tempo': 137.152, 'type': 'audio_features', 'id': '7Gibnzqw9vXDBu5zfFLQxE', 'uri': 'spotify:track:7Gibnzqw9vXDBu5zfFLQxE', 'track_href': 'https://api.spotify.com/v1/tracks/7Gibnzqw9vXDBu5zfFLQxE', 'analysis_url': 'https://api.spotify.com/v1/audio-analysis/7Gibnzqw9vXDBu5zfFLQxE', 'duration_ms': 292846, 'time_signature': 4}

class SpotifyAudioFeaturesElement(Element):
    '''
        Lookup recordings' spotify audio features
    '''

    FEATURE_WEIGHTS = {
        "danceability": 1,
        "energy": 1,
        "speechiness": 1,
        "acousticness": 1,
        "instrumentalness": 1,
        "valence": 1,
        "tempo": 1
    }

    def __init__(self):
        super().__init__()

        total_weights = 0
        for k in self.FEATURE_WEIGHTS:
            total_weights += self.FEATURE_WEIGHTS[k]

        self.weights = {}
        for k in self.FEATURE_WEIGHTS:
            self.weights[k] = self.FEATURE_WEIGHTS[k] / total_weights

    @staticmethod
    def inputs():
        return [Recording]

    @staticmethod
    def outputs():
        return [Recording]

    def compare_tracks(self, feature_index, rec0, rec1):

        features_0 = feature_index[rec0.listenbrainz["spotify_id"]]
        features_1 = feature_index[rec1.listenbrainz["spotify_id"]]

        score = 0
        for feature in self.FEATURE_WEIGHTS:
            v1 = features_0[feature]
            v2 = features_1[feature]
            score += self.weights[feature] * (fabs(v2 - v1) / ((v1 + v2) / 2.0))

        return score

    def read(self, inputs):

        spotify_ids = [r.listenbrainz["spotify_id"] for r in inputs[0]]

        sp = spotipy.Spotify(
            auth_manager=SpotifyClientCredentials(client_id=config.SPOTIFY_CLIENT_ID, client_secret=config.SPOTIFY_CLIENT_SECRET))

        features = sp.audio_features(spotify_ids)
        feature_index = { f["id"]: f for f in features }

        for i, recording in enumerate(inputs[0]):
            if i == 0:
                score = 0.0
            else:
                score = self.compare_tracks(feature_index, inputs[0][0], recording)
            recording.listenbrainz["similarity_score"] = score

        return inputs[0]
