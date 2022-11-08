#!/usr/bin/env python3
import sys

import troi.core
from troi.patches.similar_recordings import SimilarRecordingsPatch

try:
    seed_mbid = sys.argv[1]
except IndexError:
    print("Usage: similar.py [recording_mbid]")
    sys.exit(-1)

try:
    alg = sys.argv[2]
except IndexError:
    alg = "session_based_days_1095_session_300_threshold_2_limit_200"

args = {"name": "Test", "recording_mbid": seed_mbid, "algorithm": alg, "desc": "test", "echo": False, "debug": False}

playlist = troi.core.generate_playlist(SimilarRecordingsPatch(), args)

if playlist.playlists[0].recordings[0].mbid != seed_mbid:
    print("Seed track is not the first track. Could be because Spotify id was not found.")
    sys.exit(-1)

print("\nSeed recording:")
for i, recording in enumerate(playlist.playlists[0].recordings):
    if i == 1:
        print("\nSimilar recordings")

    print("  %-30s %-30s %5d %d%%" % (
        recording.name[:29],
        recording.artist.name[:29],
        recording.listenbrainz["score"],
        int(recording.listenbrainz["similarity_score"] * 100)
    ))
