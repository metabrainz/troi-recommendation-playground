MusicBrainz Elements
====================

The following elements fetch data from MusicBrainz:


troi.musicbrainz.mbid_mapping
-----------------------------

Look up a Recording in the ListenBrainz MBID mapper from only an Artist.artsit_credit_name and a Recording.name.


.. autoclass:: troi.musicbrainz.mbid_mapping.MBIDMappingLookupElement


troi.musicbrainz.mbid_reader
----------------------------

Load MBIDs from a file and return a list of Recording elements:

.. autoclass:: troi.musicbrainz.mbid_reader.MBIDReaderElement


troi.musicbrainz.recording_lookup
---------------------------------

Retrieve metadata for Recordings that have their MBID set, but other metadata is missing. This Element is useful
for taking a list of Recording MBIDs and turning them into a full set of Recording objects.

.. autoclass:: troi.musicbrainz.recording_lookup.RecordingLookupElement


troi.musicbrainz.recording
--------------------------

Given a list of Recording objects, return them from the Element. This is useful if something has generated Recordings that 
will need to be processed by Troi.

.. autoclass:: troi.musicbrainz.recording.RecordingListElement


troi.musicbrainz.year_lookup
----------------------------

Given a list of Recording objects fetch, fetch the year when they were released, using Recording.artist.name and Recording.name.

NOTE: This lookup does not use MBIDs!

.. autoclass:: troi.musicbrainz.year_lookup.YearLookupElement
