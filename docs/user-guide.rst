.. _user-guide:

User Guide
==========

Global Playlist generation
--------------------------

Once you have installed Troi, get familiar with how the command line works. To get the usage for Troi:

.. code-block:: bash

   troi --help


To list all the patches that are currently available, do:

.. code-block:: bash

   troi list


To generate a global (MBID based) playlist from a patch and display it in the terminal, do:

.. code-block:: bash

   troi playlist --print daily-jams <user_name>

This will generate a playlist and print the list to the terminal.


To generate a global playlist from a patch and display it and then upload it to ListenBrainz:

.. code-block:: bash

   troi playlist --print --upload --token <user-token> daily-jams <user_name>

This will generate a playlist and print the list to the terminal and then upload it to ListenBrainz. You can find your
user token on your `profile page at ListenBrainz <https://listenbrainz.org/profile/>`_.

From here on you can explore different :ref:`patches` or read how Troi works :ref:`technical-introduction`


Local Playlist Generation
-------------------------

Local playlists are playlists that have been resolved against a local collection
and are playable to a local player. In order for this to work, you will need
to index your local collection using the database tools first. 

**IMPORTANT**: Local playlist generation only works if you music collection is tagged with MusicBrainz tags. We recommend
`Picard <http://picard.musicbrainz.org>`_ for tagging your collection.

If you're unwilling to properly tag your collection, then please do not contact us to request that we remove
this requirement. We can't. We won't. Please close this tab and move on.


Index your music collection
^^^^^^^^^^^^^^^^^^^^^^^^^^^

If you have your collection hosted on an app like Funkwhale, Navidrome or Gonic, who have a Subsonic API, you can generate
playlists directly the web application. Alternatively, if you music collection isn't available via a Subsonic API, you can
scan a local collection of files and make local m3u playlists.

*Note*: We recommend that you scan *either* a local filesystem collection or a subsonic API hosted collection. Doing both
is going to result in erratic behaviour of the content resolver.

Setting up config.py
""""""""""""""""""""

While it isn't strictly necessary to setup **config.py**, it makes using the troi content resolver easier:

.. code-block:: bash

    cp config.py.sample config.py

Then edit **config.py** and set the location of where you're going to store your resolver database file
into **DATABASE_FILE**. If you plan to use a Subsonic API, then fill out the Subsonic section as well.

If you decide not to use the **config.py** file, make sure to pass the path to the DB file with **-d** to each
command. All further examples in this file assume you added the config file and will therefore omit  
the **-d** option.

You can also define a set of directories to be used by default for the scan command in **MUSIC_DIRECTORIES**.

Options for saving playlists
""""""""""""""""""""""""""""

The playlist generation functions below print the generated playlist and nothig else. In order to save the 
playlists or upload them, please refer to :ref:`troi-arguments`

Scanning your local filesystem collection
"""""""""""""""""""""""""""""""""""""""""

Then prepare the index and scan a music collection. mp3, m4a, wma, OggVorbis, OggOpus and flac files are supported.

.. code-block:: bash

   troi db create
   troi db scan <one or more paths to directories containing audio files>

If you configured **MUSIC_DIRECTORIES** in config file, you can just call **troi db scan**.
It should be noted paths passed on command line take precedence over this configuration.

If you remove tracks from your collection, use **cleanup** to remove references to those tracks:

.. code-block:: bash

   troi db cleanup

Scan a Subsonic collection
""""""""""""""""""""""""""

To scan a subsonic collection, you'll need to setup a config.py file. See above.

.. code-block:: bash

   troi db subsonic

This discovers the files present in the subsonic API hosted collection and adds a reference
to the local DB.

Metadata Download
"""""""""""""""""

In order to use the LB Local Radio playlist generator you'll need
to download more data for your MusicBrainz tagged music collection.

First, download tag and popularity data:

.. code-block:: bash

   troi db metadata


ListenBrainz Radio Local
^^^^^^^^^^^^^^^^^^^^^^^^

ListenBrainz's `LB Radio feature <https://listenbrainz.org/explore/lb-radio>`_
generates global playlists that can be resolved to streaming services. Troi
also supports a local version that resolved tracks against a local collection of music.

Currently artist and tag elements are supported for LB Radio Local,
which means that playlists from these two elements are made from the local 
collection and thus will not need to be resolved. All other elements
may generate playlists with tracks that are not availalble in your
collection. In this case, the fuzzy search will attempt to make the
missing tracks to your collection.

For a complete reference to LB Radio, see the :ref:`lb-radio`

The playlist generator works with a given mode: "easy", "medium"
and "hard". An easy playlist will generate data that more closely
meets the prompt, which should translate into a playlist that should
be easier and pleasent to listen to. Medium goes further and includes
less popular and more far flung stuff, before hard digs at the bottom
of the barrel. 

This may not always feel very pronounced, especially if your collection
isn't very suited for the prompt that was given.
 
 
Artist Element
""""""""""""""
 
.. code-block:: bash

   troi lb-radio easy 'artist:(taylor swift, drake)'
 
Generates a playlist with music from Taylor Swift and artists similar
to her and Drake, and artists similar to him.


Tag Element
"""""""""""

.. code-block:: bash

    troi lb-radio easy 'tag:(downtempo, trip hop)'

This will generate a playlist on easy mode for recordings that are
tagged with "downtempo" AND "trip hop".

.. code-block:: bash

    troi lb-radio medium 'tag:(downtempo, trip hop)::or'

This will generate a playlist on medium mode for recordings that are
tagged with "downtempo" OR "trip hop", since the or option was specified
at the end of the prompt.

You can include more than on tag query in a prompt:

.. code-block:: bash

   troi lb-radio medium 'tag:(downtempo, trip hop)::or tag:(punk, ska)'

Stats, Collections, Playlists and Recommended recordings
""""""""""""""""""""""""""""""""""""""""""""""""""""""""

There are more elements, but these are "global" elements that will need to 
have their results resolved to the local collection. The resolution process is
always a bit tricky since its outcome heavily depends on the collection. The
generator will do its best to generate a fitting playlist, but that doesn't
always happen. 

For the other elements, please refer to the :ref:`lb-radio`

Resolve JSPF playlists to local collection
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

First, find a playlist on ListenBrainz that you'd like to resolve to a local collection:

.. code-block:: bash

   https://listenbrainz.org/user/{your username}/playlists/

Then download the JSPF file:

.. code-block:: bash

   curl "https://api.listenbrainz.org/1/playlist/<playlist MBID>" > playlist-test.jspf

Finally, resolve the playlist to local files:

.. code-block:: bash

   troi resolve playlist-test.jspf playlist-test.m3u

Then open the m3u playlist with a local player.


Create Weekly-Jams Local Playlists
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

To create a weekly-jams recommendation playlist for a local collection run the
weekly-jams command and give the ListenBrainz username for whom you wish to create
a playlist for:

.. code-block:: bash

   troi weekly-jams <LB user name>
