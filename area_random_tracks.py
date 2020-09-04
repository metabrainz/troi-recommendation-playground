#!/usr/bin/env python3

import sys
import copy
import io
import ujson
import click

import troi.listenbrainz.area_random_recordings
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
@click.argument("area_id", required=True)
def test(area_id):
    area = troi.listenbrainz.area_random_recordings.AreaRandomTracksElement(area_id)
    r_lookup = troi.musicbrainz.recording_lookup.RecordingLookupElement()
    dump = troi.utils.DumpElement()
    playlist = troi.playlist.PlaylistElement()

    r_lookup.set_sources(area)
    playlist.set_sources(r_lookup)
    playlist.generate()
    playlist.launch()


if __name__ == "__main__":
    test()
