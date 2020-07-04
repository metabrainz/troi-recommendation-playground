#!/usr/bin/env python3

import click
import copy
import io
import ujson

import troi.listenbrainz.stats
import config


def test():
    stats = troi.listenbrainz.stats.UserArtistsElement("rob") 
    top_artists_last_week = stats.read()
    for artist in top_artists_last_week:
        print(artist)

    stats = troi.listenbrainz.stats.UserReleasesElement("rob") 
    top_releases_last_week = stats.read()
    for release in top_releases_last_week:
        print(release.artist)
        print(release)

    stats = troi.listenbrainz.stats.UserRecordingElement("rob") 
    top_recordings_last_week = stats.read()
    for recording in top_recordings_last_week:
        print(recording.artist)
        print(recording.release)
        print(recording)

#    filter = Filter()
#    top_recordings_last_week = filter.filter(top_recordings_last_week)
#    for recording in top_recordings_last_week:
#        print(recording)
#        print(recording.mb_artist['artist_credit_name'])
#        print(recording.metadata['musicbrainz'])
#        print(recording.mb_recording['recording_name'])
#        print(recording.mb_recording['recording_mbid'])
        

if __name__ == "__main__":
    test()
