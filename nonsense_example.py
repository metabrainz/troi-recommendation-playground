#!/usr/bin/env python3

import click
import copy
import io
import subprocess
import ujson

from troi import Entity, EntityEnum
from troi.lookup.mb_artist_credit import MBArtistCreditLookup
from troi.lookup.mb_recording import MBRecordingLookup
from troi.datasource.mb_related_artist_credits import MBRelatedArtistCreditsDataSource
from troi.datasource.mb_related_recordings import MBRelatedRecordingsDataSource
from troi.datafilter.mb_artist_credit_filter import MBArtistCreditFilter
from troi.operations import is_homogeneous, make_unique, union
from troi.playlist import launch_playlist
from troi.utils import print_entities
import config


def make_nonsense_playlist(recording_mbids):

    # setup components
    datasource_artist_credits = MBRelatedArtistCreditsDataSource(config.DB_CONNECT)
    datasource_recording = MBRelatedRecordingsDataSource(config.DB_CONNECT)

    lookup_artist_credit = MBArtistCreditLookup(config.DB_CONNECT)
    lookup_recording = MBRecordingLookup(config.DB_CONNECT)

    filter_artist_credit = MBArtistCreditFilter(config.DB_CONNECT)

    # Create objects for each recording argument and look them up
    recordings = [ Entity("recording", mbid) for mbid in recording_mbids ]
    lookup_recording.lookup(recordings)

    # Fetch the artist credits for each of given tracks and then find related artists for each of them
    artist_credits = [ Entity("artist-credit", recording.mb_recording['artist_credit']) for recording in recordings ]
    related_artist_credits = []
    for ac in artist_credits:
        related_artist_credits = union(related_artist_credits, datasource_artist_credits.get(ac, max_items=25))

    # Remove duplicate artist credits and sort by relevance score
    related_artist_credits = make_unique(related_artist_credits)
    related_artist_credits = sorted(related_artist_credits, key=lambda e: e.mb_artist['artist_credit_relations_count'], reverse=True)

    # For each of the provided recordings, find related recordings
    related_recordings = []
    for recording in recordings:
        related_recordings = union(related_recordings, datasource_recording.get(recording))

    # Unique and sort the list
    related_recordings = make_unique(related_recordings)
    related_recordings = sorted(related_recordings, key=lambda e: e.mb_recording['recording_relations_count'], reverse=True)
    lookup_recording.lookup(related_recordings)
  
    # Finally filter out recordings not in the related artist list
    playlist = filter_artist_credit.filter(related_recordings, related_artist_credits)

    # The "playlist" is now done. :). The rest is reporting what was done
    print("The input recordings were:")
    print_entities(recordings)

    print("Related to those artists, %d related artist_credits were loaded (5 shown):" % (len(related_artist_credits)))
    print_entities(related_artist_credits, 5)

    print("load %d related recordings to the given recordings. (5 shown):" % (len(related_recordings)))
    print_entities(related_recordings, 5)

    print("Filter related recordings by excluding tracks not in the related artists list:")
    print_entities(playlist)

    launch_playlist(playlist)



@click.command()
@click.argument("recordings", nargs=-1)
def playlist(recordings):
    make_nonsense_playlist(recordings)


def usage(command):
    with click.Context(command) as ctx:
        click.echo(command.get_help(ctx))


if __name__ == "__main__":
    playlist()
