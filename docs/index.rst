Troi Playlisting Engine
=======================

The Troi Playlisting Engine combines all of ListenBrainz' playlist efforts:

1. Playlist generation: Music recommendations and algorithmic playlist generation using a
pipeline architecture that allows easy construction of custom pipelines that output playlists.
You can see this part in action on ListenBrainz's Created for You pages, where we show of Weekly jams
and Weekly Discovery playlists. The playlist generation tools use an API-first approach were users
don't need to download massive amounts of data, but instead fetch the data via APIs as needed.

2. Local content database: Using these tools a user can scan their music collection on disk or
via a Subsonic API (e.g. Navidrome, Funkwhale, Gonic), download metadata for it and then resolve global
playlists (playlist with only MBIDs) to files available in a local collection. We also have
support for duplicate file detection, top tags in your collection and other insights.

3. Playlist exchange: We're in the process of building this toolkit out to support saving/loading playlists
in a number of format to hopefully break playlists free from the music silos (Spotify, Apple, etc)


User Guide
----------

For end-user guide on how to run Troi and what the various command line arguments are, please
see our :ref:`user-guide`.


MetaBrainz APIs for playlisting and recommendation
--------------------------------------------------

To accomplish the goal of an API-first toolkit, we, have created and hosted a number of data-sets
that can be accessed as a part of this project. From Troi you can call any API you'd like, including
the MusicBrainz and ListenBrainz APIs. We have also created the following sites with more API endpoints
to support Troi:

#. More stable APIs are hosted on our `Labs API page <https://labs.api.listenbrainz.org>`_. We work hard to ensure that these APIs stay up at all times, but we do not guarantee it. Best to not use for production.
#. More transient APIs that we do not guarantee to always be up can be found on our `data sets page <https://datasets.listenbrainz.org>`_. Do not use for production!

The ListenBrainz project offers a number of data sets:

#. Collaborative filtered recordings that suggest what recordings a user should listen to based on their previous listening habits. See the `recommended tracks for user rob <https://listenbrainz.org/recommended/tracks/rob/?page=1>`_.
#. User statistics that were derived from users recent `listening habits <https://listenbrainz.readthedocs.io/en/latest/users/api/statistics.html>`_.

We will continue to build and host more datasets as time passes. If an API endpoint becomes useful to
a greater number of people we will elevate these API endpoints to officially supported endpoints
that we ensure are up to date on online at all times.

Trivia
------

The project is named after `Deanna Troi <https://en.wikipedia.org/wiki/Deanna_Troi>`_, the empath on the
TV series Star Trek: The Next Generation.

.. toctree::
   :maxdepth: 2
   :caption: Troi Documentation Index

   installation.rst
   user-guide.rst
   troi-arguments.rst
   introduction.rst
   patches
   entities
   elements/index
   elements/musicbrainz
   elements/listenbrainz
   lb_radio.rst
   dev/index


Indices and tables
------------------

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
