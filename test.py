#!/usr/bin/env python3

from troi import Entity
from troi.lookup.mb_artist import MBArtistLookup
from troi.datasource.mb_related_artists import MBRelatedArtistsDataSource
import config

artist_mbid = "8f6bd1e4-fbe1-4f50-aa9b-94c450ec0f11"

ds = MBRelatedArtistsDataSource(config.DB_CONNECT)
al = MBArtistLookup(config.DB_CONNECT)
    
artist = Entity("artist", artist_mbid)
al.lookup(artist)

print("related artists (%s %s)" % (artist.id[:6], artist.name))
for e in ds.get(artist)[:5]:
    print("  %3d %s %s" % (e.metadata['musicbrainz']['artist_relations_count'], e.id[:6], e.name))
