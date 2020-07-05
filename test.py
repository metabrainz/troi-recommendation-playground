#!/usr/bin/env python3

import click
import copy
import io
import ujson

import troi.listenbrainz.stats
import troi.musicbrainz.msb_mapping
import troi.playlist
import config


def test():
    stats = troi.listenbrainz.stats.UserRecordingElement("rob") 
    lookup = troi.musicbrainz.msb_mapping.MSBMappingLookupElement(True)
    playlist = troi.playlist.PlaylistElement()

    stats.connect(lookup)
    lookup.connect(playlist)
    stats.push()

    playlist.launch()


if __name__ == "__main__":
    test()
