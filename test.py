#!/usr/bin/env python3

from troi import Entity
from troi.lookup.mb_artist import MBArtistLookup
from troi.lookup.mb_artist_credit import MBArtistCreditLookup
from troi.lookup.mb_recording import MBRecordingLookup
from troi.datasource.mb_related_artists import MBRelatedArtistsDataSource
from troi.datasource.mb_related_artist_credits import MBRelatedArtistCreditsDataSource
from troi.datasource.mb_related_recordings import MBRelatedRecordingsDataSource
import config

artist_mbid = "8f6bd1e4-fbe1-4f50-aa9b-94c450ec0f11"
recording_mbid = "e97f805a-ab48-4c52-855e-07049142113d"

artist_ds = MBRelatedArtistsDataSource(config.DB_CONNECT)
recording_ds = MBRelatedRecordingsDataSource(config.DB_CONNECT)
artist_credit_ds = MBRelatedArtistCreditsDataSource(config.DB_CONNECT)
artist_lookup = MBArtistLookup(config.DB_CONNECT)
artist_credit_lookup = MBArtistCreditLookup(config.DB_CONNECT)
recording_lookup = MBRecordingLookup(config.DB_CONNECT)
    
artist = Entity("artist", artist_mbid)
artist_lookup.lookup(artist)

related_artists = artist_ds.get(artist)
print("load %d related artists (%s %s)" % (len(related_artists), artist.id[:6], artist.name))
for e in related_artists[:5]:
    print("  %3d %s %s" % (e.mb_artist['artist_relations_count'], e.id[:6], e.name))
print()

recording = Entity("recording", recording_mbid)
recording_lookup.lookup(recording)


artist_credit = Entity("artist_credit", recording.mb_recording['artist_credit'])
artist_credit_lookup.lookup(artist_credit)
print("lookup artist_credit: %s" % artist_credit.name)

related_artist_credits = artist_credit_ds.get(artist_credit)
print("load %d related artist_credits (%d %s)" % (len(related_artist_credits), artist_credit.id, artist_credit.name))
for e in related_artist_credits[:5]:
    print("  %3d %7d %s" % (e.mb_artist['artist_credit_relations_count'], int(e.id), e.mb_artist['artist_name']))
print()


related_recordings = recording_ds.get(recording)
print("load %d related recordings (%s %s)" % (len(related_recordings), 
                                                 recording.id[:6], 
                                                 recording.name))
for e in related_recordings:
    print("  %3d %s %s" % (e.mb_recording['recording_relations_count'], e.id[:6], e.name))
