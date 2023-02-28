.. _entities:

Entities
========

Our entity classes are simple data containers that are laid out exactly as the entities in MusicBrainz are. The idea is that
these classes are flexible and do not require a lot of data. Usually a name and or MBID are sufficient for creating an entity.

Each of our entities have two free form dicts intended to collect data that Troi might make use of in the data pipeline:
musicbrainz and listenbrainz. If we fetch some top listened recordings from ListenBrainz, we might receive a listen_count for
that Recording. We can simply store listen_count in the listenbrainz dict and then use it in any Element in the pipeline. 

Artist
------

The Artist entity contains the name, the MBIDs and/or artist_credit_ids for a MusicBrainz artist. You can create an Artist
object with the following parameters:

.. autoclass:: troi.__init__.Artist


Release
-------

The Release entity contains the name, the MBIDs and the Artist for a MusicBrainz artist. You can create an Release
object with the following parameters:

.. autoclass:: troi.__init__.Release


Recording
---------

The Recording entity, which is the most used entity in Troi, contains the name, the MBIDs and the Artist and possible Release
for a MusicBrainz artist. You can create an Recording object with the following parameters:

.. autoclass:: troi.__init__.Recording


User
----

The User entity represents a ListenBrainz user -- this may not be very useful for anyone but the ListenBrainz team to run
Troi to generate playlists for our users:

.. autoclass:: troi.__init__.User

