#!/usr/bin/env python3
import sys

import troi.core
from troi.patches.load_audio_features import LoadAudioFeaturesPatch
from troi.listenbrainz.spotify_audio_features import SpotifyAudioFeaturesElement


def generate_playlist(args):
    playlist = troi.core.generate_playlist(LoadAudioFeaturesPatch(), args)
    if playlist is None:
        print("Could not generate playlist for %s %s" % (args["recording_mbid0"], args["recording_mbid1"]))
        return None

    if playlist.playlists[0].recordings[0].mbid != args["recording_mbid0"]:
        print("recording0 was not found at spotify")
        return None

    if playlist.playlists[0].recordings[1].mbid != args["recording_mbid1"]:
        print("recording1 was not found at spotify")
        return None

    return playlist

def print_audio_features(rec):

    print("%-30s %-30s" % (rec.name, rec.artist.name))
    for feature in SpotifyAudioFeaturesElement.FEATURE_WEIGHTS:
        print(f"  %-20s %.3f" % (feature, rec.listenbrainz["spotify_features"][feature]))

    print("")


mbid0 = sys.argv[1]
mbid1 = sys.argv[2]

args = {
    "name": "Test",
    "min_recordings": 1,
    "recording_mbid0": mbid0,
    "recording_mbid1": mbid1,
    "desc": "test",
    "echo": False,
    "debug": False
}
s = generate_playlist(args)
if not s:
    print("Fail. you brought this in yourself, now suffer.")
    sys.exit(-1)

rec0 = s.playlists[0].recordings[0]
rec1 = s.playlists[0].recordings[1]

print_audio_features(rec0)
print_audio_features(rec1)

print("Audio feature similarity score: %d%%" % int(rec1.listenbrainz["similarity_score"] * 100))
