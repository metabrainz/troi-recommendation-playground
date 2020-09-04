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
import troi.tools.area_lookup
import troi.playlist
import troi.utils
import troi.operations

@click.group()
def cli():
    pass

@cli.command()
@click.argument("area_name", required=True)
@click.argument("start_year", required=False, type=int, default=0)
@click.argument("end_year", required=False, type=int, default=3000)
def test(area_name, start_year, end_year):

    try:
        area_id = troi.tools.area_lookup.area_lookup(area_name)
    except RuntimeError as err:
        print("Cannot lookup area: ", str(err))
        return

    area = troi.listenbrainz.area_random_recordings.AreaRandomTracksElement(area_id, start_year, end_year)
    r_lookup = troi.musicbrainz.recording_lookup.RecordingLookupElement()
    dump = troi.utils.DumpElement()
    playlist = troi.playlist.PlaylistElement()

    r_lookup.set_sources(area)
    playlist.set_sources(r_lookup)
    playlist.generate()

    playlist.print()
    print("-- generated playlist with %d recordings. Open playlist by opening playlist.html in your browser." % len(playlist.entities))
    playlist.launch()


if __name__ == "__main__":
    test()
