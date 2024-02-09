.. _technical-introduction:

Playlist generation technical Introduction
==========================================

Patches
-------

A patch (data pipeline) is constructed by instantiating Element objects and then chaining them
together with set_sources() methods. If you want to create a patch with two elements, the following
code could be used:

.. code-block:: python

   element0 = MyElement()
   element1 = MyOtherElement()
   element1.set_sources(element0)

The most common data passed through a data are Recording objects that represent a MusicBrainz recording.
But other data elements such as Users, Artists and Releases could easily be objects passed through a pipeline.
For instance, to create a Recording object, you'll need to at least pass in a name of the Recording:

.. autoclass:: troi.__init__.Recording
    :noindex:

Very often Recordings are created with name and mbid arguments and then the 
:py:class:`~troi.musicbrainz.recording_lookup.RecordingLookupElement` is used to automatically lookup all the
needed data (e.g. artist).

A patch never processes data on its own -- a Patch returns a constructed pipeline of Elements that are chained 
together. The Elements are the classes that process data, but those are invoked only after the pipeline
is constructed and when Troi begins to generate a playlist.

If is not uncommon to have a PlaylistRedundancyReducerElement at the end of the pipeline
which returns a Playlist object of the desired length with a limit to the number of times a single
artist's tracks can be included in the playlist.


Entities
--------

The pre-defined elements User, Artist, Release, Recording all have elements of MBID and name. A recording
also had an Artist element included for obvious reasons. The Artist element actually contains support
for more than one artist, so its MBID element is actually plural MBIDS in order to accurately represent
a MusicBrainz Artist Credit. Each of these objects contains two free form dicts: musicbrainz and listenbrainz.
When you fetch data that doesn't fit into the predefined fields of the data object classes, that data can be
stored in these free form dicts. For instance, a Recording element that was loaded from ListenBrainz
statistics will have a listen_count field.


Elements
--------

Troi uses a pipeline architecture comprised of Elements (a node in the pipeline) that can be chained
togther. Each element :py:class:`~troi.__init__.Element` can be a source of data and act like a filter that takes the incoming data,
acts on it and passes output data. At the end of the pipeline, the last element should return
a Playlist object that the Troi main function can then display or submit to ListenBrainz or other
services.

The important methods of this class are:

.. autoclass:: troi.__init__.Element
    :members: inputs, outputs, set_sources
    :noindex:

Each class derived from Element must override these three functions.
