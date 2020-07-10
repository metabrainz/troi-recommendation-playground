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
import troi.operations
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
    # Create elements
    mfccsw = troi.acousticbrainz.annoy.AnnoyLookupElement("mfccsw", "145f5c43-0ac2-4886-8b09-63d0e92ded5d") 
    gfccsw = troi.acousticbrainz.annoy.AnnoyLookupElement("gfccsw", "145f5c43-0ac2-4886-8b09-63d0e92ded5d") 
    moods = troi.acousticbrainz.annoy.AnnoyLookupElement("moods", "145f5c43-0ac2-4886-8b09-63d0e92ded5d") 
    r_lookup = troi.musicbrainz.recording_lookup.RecordingLookupElement(config.DB_CONNECT)
    dump = troi.utils.DumpElement()

    intersect1 = troi.operations.IntersectionElement()
    intersect2 = troi.operations.IntersectionElement()

    # Connect elements
    intersect1.set_sources([mfccsw, gfccsw])
#    intersect2.set_sources([moods, intersect1])
    r_lookup.set_sources(intersect1)
    dump.set_sources(r_lookup)
    dump.generate()

if __name__ == "__main__":
    ab_similarity_test()
