#!/usr/bin/env python3

from troi import Entity
from troi.lookup.mb_artist import MBArtistLookup
from troi.lookup.mb_recording import MBRecordingLookup
from troi.datasource.mb_related_artists import MBRelatedArtistsDataSource
from troi.datasource.mb_related_recordings import MBRelatedRecordingsDataSource
import config

artist_mbid = "8f6bd1e4-fbe1-4f50-aa9b-94c450ec0f11"
recording_mbid = "e97f805a-ab48-4c52-855e-07049142113d"

artist_ds = MBRelatedArtistsDataSource(config.DB_CONNECT)
recording_ds = MBRelatedRecordingsDataSource(config.DB_CONNECT)
al = MBArtistLookup(config.DB_CONNECT)
rl = MBRecordingLookup(config.DB_CONNECT)
    
artist = Entity("artist", artist_mbid)
al.lookup(artist)

related_artists = artist_ds.get(artist)
print("load %d related artists (%s %s)" % (len(related_artists), artist.id[:6], artist.name))
for e in related_artists[:5]:
    print("  %3d %s %s" % (e.musicbrainz['artist']['artist_relations_count'], e.id[:6], e.name))

recording = Entity("recording", recording_mbid)
rl.lookup(recording)

related_recordings = recording_ds.get(recording)
print()
print("load %d related recordings (%s %s)" % (len(related_recordings), 
                                                 recording.id[:6], 
                                                 recording.name))
for e in related_recordings:
    print("  %3d %s %s" % (e.musicbrainz['recording']['recording_relations_count'], e.id[:6], e.name))
