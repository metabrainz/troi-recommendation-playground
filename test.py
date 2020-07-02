#!/usr/bin/env python3

import click
import copy
import io
import subprocess
import ujson

from troi import Entity, EntityEnum
from troi.datasource.lb_stats import ListenBrainzStatsDataSource as Stats
from troi.datafilter.msb_mapping import MSBMappingFilter as Filter
import config

def test():
    stats = Stats("rob", "recording", "week")
    top_recordings_last_week = stats.get()

    filter = Filter()
    top_recordings_last_week = filter.filter(top_recordings_last_week)
    for recording in top_recordings_last_week:
        print(recording)
        print(recording.mb_artist['artist_credit_name'])
        print(recording.metadata['musicbrainz'])
        print(recording.mb_recording['recording_name'])
        print(recording.mb_recording['recording_mbid'])
        

if __name__ == "__main__":
    test()
