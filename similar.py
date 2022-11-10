#!/usr/bin/env python3
import sys

import troi.core
from troi.patches.similar_recordings import SimilarRecordingsPatch

DATASETS = [
    "session_based_days_730_session_200_contribution_3_threshold_5_limit_100_filter_True",
    "session_based_days_365_session_400_contribution_5_threshold_5_limit_100_filter_True",
    "session_based_days_730_session_400_contribution_1_threshold_5_limit_100_filter_True",
    "session_based_days_730_session_400_contribution_3_threshold_5_limit_100_filter_True",
    "session_based_days_365_session_200_contribution_3_threshold_5_limit_100_filter_True",
    "session_based_days_365_session_400_contribution_1_threshold_5_limit_100_filter_True",
    "session_based_days_730_session_200_contribution_5_threshold_5_limit_100_filter_True",
    "session_based_days_730_session_300_contribution_1_threshold_5_limit_100_filter_True",
    "session_based_days_365_session_400_contribution_3_threshold_5_limit_100_filter_True",
    "session_based_days_730_session_400_contribution_5_threshold_5_limit_100_filter_True",
    "session_based_days_365_session_200_contribution_1_threshold_5_limit_100_filter_True",
    "session_based_days_365_session_200_contribution_5_threshold_5_limit_100_filter_True",
    "session_based_days_730_session_300_contribution_5_threshold_5_limit_100_filter_True",
    "session_based_days_365_session_300_contribution_5_threshold_5_limit_100_filter_True",
    "session_based_days_730_session_200_contribution_1_threshold_5_limit_100_filter_True",
    "session_based_days_365_session_300_contribution_3_threshold_5_limit_100_filter_True",
    "session_based_days_365_session_300_contribution_1_threshold_5_limit_100_filter_True",
    "session_based_days_730_session_300_contribution_3_threshold_5_limit_100_filter_True"
]

RECORDING_MBIDS = [
    "18729faf-50e2-4217-b473-e96d518e7496",
    "e97f805a-ab48-4c52-855e-07049142113d",
    "97e69767-5d34-4c97-b36a-f3b2b1ef9dae",
    "176ce892-5deb-457b-b3a2-d947c45ac712",
    "7f527f79-3303-4f30-add1-3b58b65181d9",
    "8e74dd9d-e5a3-4acd-918a-c36a0f8cda84",
    "af87f70f-14e1-452b-ba66-b3e1be7fbdf1",
    "17f470ae-538c-4494-a5d1-1873c3a0c7e2",
    "822c0580-a87e-43e0-a347-bfc5b3e2ef49",
    "a8daf397-53e3-41af-aad5-ab7e50fb438a",
    "ffb6e773-2d24-420c-90ce-36b6025f31e2",
    "bd0ef97e-edb6-4479-95ad-0c1957edf77b",
    "13d3bf6a-63ff-449f-873c-dcf279801d36",
    "a423504f-8919-43be-9bdc-aaa3a1585868",
    "71209300-34e5-491d-81ad-76237d167604",
    "6d418e64-c194-47d4-9172-306919a6fc9f"
]


def generate_playlist(args):
    playlist = troi.core.generate_playlist(SimilarRecordingsPatch(), args)
    if playlist is None:
        print("Could not generate playlist for %s %s" % (args["recording_mbid"], args["algorithm"]))
        return None

    if playlist.playlists[0].recordings[0].mbid != args["recording_mbid"]:
        print("Seed track is not the first track. Could be because Spotify id was not found.")
        return None

    score = 0.0
    for r in playlist.playlists[0].recordings:
        score += r.listenbrainz["similarity_score"]

    return score / len(playlist.playlists[0].recordings)


def print_playlist(playlist):

    print("\nSeed recording:")
    for i, recording in enumerate(playlist.playlists[0].recordings):
        if i == 1:
            print("\nSimilar recordings")

        print("  %-30s %-30s %5d %d%%" % (recording.name[:29], recording.artist.name[:29], recording.listenbrainz["score"],
                                          int(recording.listenbrainz["similarity_score"] * 100)))

results = {}
for alg in DATASETS:
    score = 0.0
    for mbid in RECORDING_MBIDS:
        args = {"name": "Test", "recording_mbid": mbid, "algorithm": alg, "desc": "test", "echo": False, "debug": False}
        s = generate_playlist(args)
        if s is None:
            continue

        lowest_score = 100
        for recording in playlist.playlists[0].recordings:
            lowest_score = min(lowest_score, recording.listenbrainz["similarity_score"])

    results[alg] = s

for alg, score in sorted(results.items(), key=lambda item: item[1], reverse=True):
    print("%4d%% %s" % (int(score*100), alg))
