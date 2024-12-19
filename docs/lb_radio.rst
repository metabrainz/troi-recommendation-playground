.. _lb-radio:

LB Radio Prompt Reference
=========================

ListenBrainz Radio is a powerful playlist/radio generation tool that gives users a lot of power to
automatically make playlists. The troi toolkit offers two types of LB Radio playlists: Global and local. Global
playlists generated with the lb-radio patch via the playlist command are made from all the available recorings
available in MusicBrainz and contain only MusicBrainz MBIDs. Normal music players cannot play these playlists. LB Radio
Local creates local playlists that are fully resolved against a local playlist and when converted to the m3u format
are playable with a local playlist.

To generate a playlist, the user will need to enter an "LB Radio prompt", which is a type of search query that specifies
what music should be added to the playlist. A Radio prompt is composed of one or more terms, taking the form:

::

  entity:values:weight:option


Each term generates a stream of recordings and recordings from each of the streams are then interleaved to make a single playlist.
The optional weight argument allows the user to control how often this term
will contribute to the final playlist. By default each term gets a value of 1, if the user didn't specify a weight value.
A term with a weight of 3 will contribute 3 times more recordings than a term with weight 1. The final part of each term
are options, documented in the options section.

Entities
--------

The LB Radio supports the following entities:

#. **artist**: Play tracks from this artists and similar artists
#. **tag**: Play tracks from one of more tags
#. **collection**: Use a MusicBrainz collection as a source of recordings. (mode does not apply to collections)
#. **playlist**: Use a ListenBrainz playlist as a source of recordings. (mode also does not apply to playlists)
#. **stats**: Use a ListenBrainz user's statistics as a source of recordings.
#. **recs**: Use a ListenBrainz user's recommended recordings as a source of recordings.
#. **country**: Select recordings from artists who are from the given country.

Options
-------

All terms have the following options:

#. **easy**: Use easy mode for this term. See modes below.
#. **medium**: Use medium mode for this term.
#. **hard**: Use hard mode for this term.

For artist and tag terms, the following option applies:

#. **nosim**: Do not add similar artists/tags, only output recordings from the given artist/tag.

For tag queries, the following options exist:

#. **and**: For a tag query, if "and" is specified (the default) recordings will be chosen if all the given tags are applied to that recording.
#. **or**: For a tag query, if "or" is specified, then recordings will be chosen if any of the tags are applied to the recording.
#. **nosim**: Tag queries on medium and hard mode may include similar tags. Specifying nosim for a tag query ensures that no similar tags are used.

For the stats term, the following options apply:

#. **week**, **month**, **quarter**, **half_yearly**, **year**: Stats for the user for the past week, month, quarter, half_yearly, year, respectively.
#. **all_time**: Stats for all time, covering all listens for the user.
#. **this_week**, **this_month**, **this_year**: Stats for the user for the current week, month, year, respectively.

For the recs term, the following options apply:

#. **listened**: Fetch recommeded recordings that the user has listened to. Useful for making "safe" playlists.
#. **unlistened**: Fetch recommeded recordings that the user has not listened to. Useful for making "exploration" playlists.

Modes
-----

Along with a prompt, the user will need to specify which mode they would like to use to generate the playlist: easy, medium or hard.

The core functionality of LB radio is to intelligently, yet sloppily, pick from vast lists of data to form pleasing playlists. Almost all
of the data sources (similar artists, top recordings of an artist, user stats, etc) are ordered lists of data, with the most relevant data
near the top and less revelvant data near the bottom. Broadly speaking, the three modes divide each of these datasets into three chunks: easy 
mode will focus on the most relevant data, medium on the middle relevant data and hard on the tail end.

For almost all of the source entities (see above), this applies in a pretty staightforward manner: Whenever an ordered list of data
exists, we use the modes to inform which section of data we look at. However, the tag element is an entirely different beast. Roughly speaking,
easy mode attempts to fetch recordings tagged with the given tag, medium mode picks tags from release/release-group tags and hard mode picks
tagged recordings from artists. In reality there are a lot more nuances in this process. What if there aren't enough tracks to make a reliable easy
playlist? Then don't make one and let the user know they could try again on medium mode and that they would get a playlist. There are other heuristics
baked into the tag query that are not easy to describe and quite likely will change in the near future as we respond to community feedback. Once
we're comfortable that the tag entities is working well, we will improve these docs.

This idea of modes comes from video games, where players can choose how hard the game should be to play. In the context of LB Radio,
the resultant playlist will also be more work to listen to the harder the mode. Which mode to use is entirely up to the user -- easy
is likely going to create a playlist with familiar music, and a hard playlist may expose you to less familiar music.

Syntax Notes
------------

Artist and tag names are the tricky bits to specify in a prompt, so they must be enclosed with ():

::

  artist:(Blümchen)
  tag:(deep house)
  artist:(Мумий Тролль)

Furthermore, artist names must be spelled exactly as their appear in MusicBrainz. If you have difficulty specifying the
correct artist, you can use an artist MBID to be very precise.

Tags have similar restrictions. If a tag you'd like to specify has no spaces or non-latin unicode characters you may use:

::

  tag:(punk)
  #punk

But with spaces or non-latin unicode characters, wrap it in () and use the full tag element name:

::

  tag:(hip hop)

::

  tag:(あなたを決して裏切りません)


Simple examples
---------------

::

  Rick Astley

Create a single stream, from artist Rick Astley and similar artists. Artist names must be spelled here exactly as they are
spelled in MusicBrainz. If for some reason the artist name is not recognized, specify an MBID instead. See below.


::

  #punk

The # shorthand notation allows user to quickly specify a tag radio, but it only works for one tag and the tag cannot contain spaces. For
more advanced prompts, use the full notation described above.

::

  tag:(rock,pop)::or

This prompt generates a playlist with recordings that have been tagged with either the "rock" OR "pop" tags. The weight can be omitted and will
be assumed to be 1.

::

  tag:(rock) tag:(pop)

Create two streams, one from tag "rock" contributing 3 parts of the recordings and one from tag "pop" contibuting 2 parts of the recordings.

::

  tag:(trip hop)

Tags that have a space in them must be enclosed in (). Specifying multiple tags requires the tags to be enclosed in () as well as comma separated.

::

  tag:(trip hop, downtempo)

If LB-radio does not find your artist, you can specify an artist using an Artist MBID:

::

  artist:(8f6bd1e4-fbe1-4f50-aa9b-94c450ec0f11)

LB-radio also supports MusicBrainz collections as sources:

::

  collection:(8be1a919-a386-45f3-8cc2-0d9249b02aa4)

Will select random recordings from a MusicBrainz recording collection -- the modes wont have any affect on collections, since
collections have no inherent ranking that could be used to select recordings according to mode. :(


::

  playlist:(8be1a919-a386-45f3-8cc2-0d9249b02aa4)

Will select random recordings from a ListenBrainz playlist -- the modes wont have any affect on collections, since
plylists have no inherent ranking that could be used to select recordings according to mode. :(


::

  stats:lucifer::all_time

Will select random recordings from the ListenBrainz user lucifer recordings statistics for all time. 


::

  recs:mr_monkey::unlistened

Will select random recordings from the ListenBrainz user mr_monkey's recommended recordings that mr_monkey hasn't listened to.

::

  country:(Mali)

Will select random recordings from artists who are from the given country. While this features generally represents music from
that selected country, some artists leave their home country and don't perform music representative of their country, so 
this element may not always be 100% on point. But it can still create some very interesting playlists!


More complex examples
---------------------

::

  artist:(pretty lights):3:easy tag:(trip hop):2 artist:(morcheeba)::nosim

This prompt will play 3 parts from artist "Pretty Lights", 2 parts from the tag "trip hop" and 1 part from the artist "Morcheeba" with no
tracks from similar artists.

::

  tag:(deep house):2:medium tag:(metal):1:hard artist:(blümchen):2:easy

This will play 2 parts from tag "deep house" on medium mode, 1 part from tag "metal" on hard mode and 2 parts from artists "Blümchen" on easy mode.
