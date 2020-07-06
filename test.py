#!/usr/bin/env python3

import click
import copy
import io
import ujson

import troi.listenbrainz.stats
import troi.acousticbrainz.annoy
import troi.musicbrainz.msb_mapping
import troi.musicbrainz.recording_lookup
import troi.playlist
import troi.utils
import config


def lb_stats_test():
    stats = troi.listenbrainz.stats.UserRecordingElement("rob") 
    lookup = troi.musicbrainz.msb_mapping.MSBMappingLookupElement(True)
    playlist = troi.playlist.PlaylistElement()

    stats.connect(lookup)
    lookup.connect(playlist)
    stats.push()

    playlist.print()


def ab_similarity_test():
    sim = troi.acousticbrainz.annoy.AnnoyLookupElement("mfccsw", "145f5c43-0ac2-4886-8b09-63d0e92ded5d") 
    r_lookup = troi.musicbrainz.recording_lookup.RecordingLookupElement(config.DB_CONNECT)
    dump = troi.utils.DumpElement()
    sim.connect(r_lookup)
    r_lookup.connect(dump)
    sim.push([])

if __name__ == "__main__":
    ab_similarity_test()
