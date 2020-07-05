#!/usr/bin/env python3

import click
import copy
import io
import ujson

import troi.listenbrainz.stats
import troi.musicbrainz.msb_mapping
import config


def test():
    stats = troi.listenbrainz.stats.UserRecordingElement("rob") 
    top_recordings_last_week = stats.read()
#    for recording in top_recordings_last_week:
#        print(recording.artist)
#        print(recording.release)
#        print(recording)

    lookup = troi.musicbrainz.msb_mapping.MSBMappingLookupElement(True)
    top_recordings_last_week = lookup.read(top_recordings_last_week)
    for recording in top_recordings_last_week:
        print(recording.artist.name)
        print(recording.artist.artist_credit_id)
        print(recording.name)
        print(recording.mbid)
        print()
        

if __name__ == "__main__":
    test()
