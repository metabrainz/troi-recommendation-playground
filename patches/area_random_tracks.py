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
import troi.patch
import troi.utils
import troi.operations

class AreaRandomRecordingsPatch(troi.patch.Patch):

    def inputs(self):
        return [(str, "area"), (int, "start year"), (int, "end year")]

    def slug(self):
        return "area-random-recordings"

    def description(self):
        return "Generate a list of random recordings from a given area."

    def run(self, inputs):

    def test(area_name, start_year, end_year):

        area_name = inputs[0]
        start_year = inputs[1]
        end_year = inputs[2]

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
