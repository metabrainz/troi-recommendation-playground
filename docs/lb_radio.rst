LB Radio Prompt Reference
=========================

ListenBrainz Radio is a powerful playlist/radio generation tool that gives users a lot of power to
automatically make playlists.

To generate a playlist, the user will need to enter an "LB Radio prompt", which is a type of search query that specifies
what music should be added to the playlist. A Radio prompt is composed of one or more terms, taking the form:

::

  entity:values:weight:option


Each term generates a stream of recordings and each of the streams are then interleaved to make a single playlist. The
entity must be either "artist" or "tag" currently. The weight argument allows the user to control how often this term
will contribute to the final playlist. By default each term gets a value of 1, if the user didn't specify a weight value.
A term with a weight of 3 will contribute 3 times more recordings than a term with weight 1. The final part of each term
are options:


#. **nosim**: Do not add similar artists, only output recordings from the given artist.
#. **and**: For a tag query, if "and" is specified (the default) recordings will be chosen if all the given tags are applied to that recording.
#. **or**: For a tag query, if "or" is specified, then recordings will be chosen if any of the tags are applied to the recording.
#. **easy**: Use easy mode for this term. See modes below.
#. **medium**: Use medium mode for this term.
#. **hard**: Use hard mode for this term.


Modes
-----

Along with a prompt, the user will need to specify which mode they would like to use to generate the playlist: easy, medium or hard.
In easy mode, only recordings from and similar artists are chosen that are strongly related to the seed artists/seed tag. In medium 
mode, recordings and similar artists are chosen that have a medium relation and in hard mode, the recordings and similar artists with
low relations will be chosen.

This idea comes from video games, where players can choose how hard the game should be to play. In the context of LB Radio,
the resultant playlist will also be more work to listen to the harder the mode. Which mode to use is entirely up to the user -- easy
is likely going to create a playlist with familiar music, and a hard playlist may expose you to less familiar music.


Simple examples
---------------

::

  artist:(Rick Astley)

Create a single stream, from artist Rick Astley and similar artists. Artist names must be spelled here exactly as they are
spelled in MusicBrainz. If for some reason the artist name is not recognized, specify an MBID instead. See below.

::

  tag:rock:3 tag:pop:2

Create two streams, one from tag "rock" contributing 3 parts of the recordings and one from tag "pop" contibuting 2 parts of the recordings.

::

  artist:8f6bd1e4-fbe1-4f50-aa9b-94c450ec0f11


Specify an exact artist, using an artist MBID.

::

  #rock #pop


The # shorthand notation allows user to quickly specify a tag radio. This prompt generates two equal streams from the tags "rock" and "pop".

::

  #(rock,pop)
  tag:(rock,pop)

These two prompts are equal, the # notation is simply a shortcut for tag. This prompt generates a playlist with recordings that have been tagged
with both the "rock" AND "pop" tags.

::

  tag:(rock,pop):1:or

This prompt generates a playlist with recordings that have been tagged with either the "rock" OR "pop" tags. The weight 1 must be specified
in order to specify the or option.

::

  tag:(trip hop)

Tags that have a space in them must be enclosed in (). Specifying multiple tags requires the tags to be enclosed in () as well as comma separated.

::

  collection:8be1a919-a386-45f3-8cc2-0d9249b02aa4

Will select random recordings from a recording collection -- the modes wont have much affect on collections, since collections have no inherent
ranking that could be used to select recordings according to mode. :(


More complex examples
---------------------

::

  artist:(pretty lights):3:easy tag:(trip hop):2 artist:morcheeba:1:nosim

This prompt will play 3 parts from artist "Pretty Lights", 2 parts from the tag "trip hop" and 1 part from the artist "Morcheeba" with no
tracks from similar artists.

::

  tag:(deep house):2:medium tag:(metal):1:hard artist:blümchen:2:easy

This will play 2 parts from tag "deep house" on medium mode, 1 part from tag "metal" on hard mode and 2 parts from artists "Blümchen" on easy mode.
