#!/usr/bin/env python3

import sys
import copy
import io
import ujson
import click

import troi.listenbrainz.stats
import troi.listenbrainz.recs
import troi.acousticbrainz.annoy
import troi.musicbrainz.msb_mapping
import troi.musicbrainz.recording_lookup
import troi.playlist
import troi.utils
import troi.operations

@click.group()
def cli():
    pass

@cli.command()
@click.argument("user", required=True)
@click.argument("type", type=click.Choice(['top', 'similar']), default="top")
def recommended_recordings(user, type):
    recs = troi.listenbrainz.recs.UserRecordingRecommendationsElement(user_name=user, artist_type=type, count=25)
    r_lookup = troi.musicbrainz.recording_lookup.RecordingLookupElement()
    dump = troi.utils.DumpElement()
    playlist = troi.playlist.PlaylistElement()

    r_lookup.set_sources(recs)
    playlist.set_sources(r_lookup)
    playlist.generate()
    playlist.launch()


if __name__ == "__main__":
    recommended_recordings()
