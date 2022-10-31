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

print("\nSeed recording:")
for i, recording in enumerate(playlist.playlists[0].recordings):
    if i == 1:
        print("\nSimilar recordings")

    genres = set(recording.musicbrainz.get("tag", []) +
                 recording.artist.musicbrainz.get("tag", []) +
                 recording.release.musicbrainz.get("tag", []))
    genres = ",".join(sorted(list(genres)))

    print("  %-30s %-30s %5d %s" % (
        recording.name[:29],
        recording.artist.name[:29],
        recording.musicbrainz["score"],
        genres
    ))
