# Introduction

The Troi Playlisting Engine combines all of ListenBrainz' playlist efforts:

1. Playlist generation: Music recommendations and algorithmic playlist generation using a
pipeline architecture that allows easy construction of custom pipelines that output playlists.
You can see this part in action on ListenBrainz's Created for You pages, where we show of Weekly jams
and Weekly Discovery playlists. The playlist generation tools use an API-first approach were users
don't need to download massive amounts of data, but instead fetch the data via APIs as needed.

2. Local content database: Using these tools a user can scan their music collection on disk or
via a Subsonic API (e.g. Navidrome, Funkwhale, Gonic), download metadata for it and then resolve global
playlists (playlist with only MBIDs) to files available in a local collection.

3. Playlist exchange: We're in the process of building this toolkit out to support saving/loading playlists
in a number of format to hopefully break playlists free from the music silos (Spotify, Apple, etc)

The project is named after [Deanna Troi](https://en.wikipedia.org/wiki/Deanna_Troi).

## Features

### Playlist generation

Troi's can be used to generate playlists:

1. A pipelined architecture for creating playlists from any number of sources.
2. Data sources that fetch data from APIs and feed the data into the troi pipelines.
3. Pipeline elements that are connected together are called Patches. Troi includes a number of built-in patches.
4. The largest patch implements ListenBrainz radio that can generate "radio style" playlists based on one or more
artists, tags, user statistics, user recommendations, LB playlists and MB collections.
5. Generated playlists are output in the JSPF format, the JSON version of XPSF playlists.

Troi is being used to generate weekly recommendations on ListenBrainz (weekly jams, weekly exploration)
as well as [LB Radio](https://listenbrainz.org/explore/lb-radio/).

#### Data-sets

To accomplish this goal, we, the MetaBrainz Foundation, have created and hosted a number of data-sets
that can be accessed as a part of this project. For instance, the more stable APIs are hosted on our
[Labs API page](https://labs.api.listenbrainz.org).

ListenBrainz offers a number of data sets:

1. Collaborative filtered recordings that suggest what recordings a user should listen to based on their previous listening habits.
2. User statistics that were derived from users recent listening habits.
3. Listening stats that can be used as a measure of popularity.
4. Similarity data for artists and recordings

We will continue to build and host more datasets as time passes. If an API endpoint becomes useful to
a greater number of people we will elevate these API endpoints to officially supported endpoints
that we ensure are up to date on online at all times.

### Database / Content Resolution

The ListenBrainz Content Resolver resolves global JSPF playlists to
a local collection of music, using the content resolver.

The features include:

1. ListenBrainz Radio Local: allows you to generate radio-style playlists that
that are created using only the files in the local collection, or if that is not
possible, a global playlist with MBIDS will be resolved to a local file collection
as best as possible.

2. Periodic-jams: ListenBrainz periodic-jams, but fully resolved against your own
local collection. This is optimized for local and gives better results than
the global troi patch by the same name.

3. Resolve global playlists (usually JSPF files with MusicBrainz IDs) to a local collection
of music.

4. Metadata fetching: Several of the features here require metadata to be downloaded
from ListenBrainz in order to power the LB Radio Local.

5. Scan local file collections. MP3, Ogg Vorbis, Ogg Opus, WMA, M4A and FLAC file are supported.

6. Scan a remote subsonic API collection. We've tested Navidrome, Funkwhale and Gonic.

7. Print a report of duplicate files in the collection

8. Print a list of top tags for the collection

9. Print a list of tracks that failed to resolve and print the list of albums that they
belong to. This gives the user feedback about tracks that could be added to the collection
to improve the local matching.

## Documentation

Full documentation for Troi is available at [troi.readthedocs.org](https://troi.readthedocs.org).

### Installation for end users

Troi is available for download via [PyPi](https://pypi.org/project/troi/).

### Installation for Development

**Linux and Mac**

```
virtualenv -p python3 .ve
source .ve/bin/activate
pip3 install -e .[tests]
troi --help
```

**Windows**

```
virtualenv -p python .ve
.ve\Scripts\activate.bat
pip install -e .[tests]
troi --help
```

### Playlist commands

List available patches:

    troi list

Generate a playlist using a patch:

    troi playlist --print [patch-name]

If the patch requires arguments, running it with no arguments will print a usage statement, e.g.

    $ troi playlist lb-radio
        Usage: lb-radio [OPTIONS] MODE PROMPT

          Generate a playlist from one or more Artist MBIDs

          MODE which mode to generate playlists in. must be one of easy, mediumedium, hard
          PROMPT is the LB radio prompt. See troi/parse_prompt.py for details.

        Options:
          --help  Show this message and exit.

To generate an LB Radio playlist on easy mode with an artist and a tag, use the following:

    troi playlist lb-radio easy "artist:(pretty lights) tag:(chillwave)"

The use the --upload and --token options to upload the playlist to ListenBrainz.

### Database Features

#### Setting up config.py

While it isn't strictly necessary to setup `config.py`, it makes using the resolver easier:

```
cp config.py.sample config.py
```

Then edit `config.py` and set the location of where you're going to store your resolver database file
into `DATABASE_FILE`. If you plan to use a Subsonic API, then fill out the Subsonic section as well.

If you decide not to use the `config.py` file, make sure to pass the path to the DB file with `-d` to each
command. All further examples in this file assume you added the config file and will therefore omit
the `-d` option.

You can also define a set of directories to be used by default for the scan command in `MUSIC_DIRECTORIES`.

### Command-line help

You can list all available commands using:

```
troi db --help
```

You can get help on a specific command using:

```
troi db <command> --help
```

### Scanning your collection

Note: Soon we will eliminate the requirement to do a filesystem scan before also doing a subsonic
scan (if you plan to use subsonic). For now, do the file system scan, then the subsonic scan.

#### Scan a collection on the local filesystem

Then prepare the index and scan a music collection. mp3, m4a, wma, OggVorbis, OggOpus and flac files are supported.

```
troi db create
troi db scan <one or more paths to directories containing audio files>
```

If you configured `MUSIC_DIRECTORIES` in config file, you can just call `resolve scan`.
It should be noted paths passed on command line take precedence over this configuration.

If you remove tracks from your collection, use `cleanup` to remove references to those tracks:

```
troi db cleanup
```

#### Scan a Subsonic collection

To scan a subsonic collection, you'll need to setup a config.py file. See above.

```
resolve subsonic
```

This will match your collection to the remove subsonic API collection.

### Resolve JSPF playlists to local collection

Then make a JSPF playlist on LB:

```
https://listenbrainz.org/user/{your username}/playlists/
```

Then download the JSPF file (make sure the playlist is public):

```
curl "https://api.listenbrainz.org/1/playlist/<playlist MBID>" > test.jspf
```

Finally, resolve the playlist to local files:

```
troi resolve input.jspf output.m3u
```

Then open the m3u playlist with a local tool.

### Create playlists with ListenBrainz Local Radio

#### Prerequisites

NOTE: This feature only works if you music collection 
is tagged with MusicBrainz tags. We recommend Picard:
http://picard.musicbrainz.org for tagging your collection.

If you're unwilling to properly tag your collection,
then please do not contact us to request that we remove
this requirement. We can't. We won't. Please close this 
tab and move on.

If you have your collection hosted on an app like Funkwhale,
Navidrome or Gonic, who have a Subsonic API, you can generate
playlists directly the web application.

### Setup

In order to use the LB Local Radio playlist generator you'll need
to download more data for your MusicBrainz tagged music collection.

First, download tag and popularity data:

```
resolve metadata
```

#### Playlist generation

Currently artist and tag elements are supported for LB Local Radio,
which means that playlists from these two elements are made from the local 
collection and thus will not need to be resolved. All other elements
may generate playlists with tracks that are not availalble in your
collection. In this case, the fuzzy search will attempt to make the
missing tracks to your collection.

For a complete reference to LB Radio, see:
[ListenBrainz Radio Docs](https://troi.readthedocs.io/en/latest/lb_radio.html)

The playlist generator works with a given mode: "easy", "medium"
and "hard". An easy playlist will generate data that more closely
meets the prompt, which should translate into a playlist that should
be easier and pleasent to listen to. Medium goes further and includes
less popular and more far flung stuff, before hard digs at the bottom
of the barrel. 

This may not always feel very pronounced, especially if your collection
isn't very suited for the prompt that was given.


##### Artist Element

```
troi lb-radio easy 'artist:(taylor swift, drake)'
```

Generates a playlist with music from Taylor Swift and artists similar
to her and Drake, and artists similar to him.


##### Tag Element

```
resolve lb-radio easy 'tag:(downtempo, trip hop)'
```

This will generate a playlist on easy mode for recordings that are
tagged with "downtempo" AND "trip hop".

```
resolve lb-radio medium 'tag:(downtempo, trip hop)::or'
```

This will generate a playlist on medium mode for recordings that are
tagged with "downtempo" OR "trip hop", since the or option was specified
at the end of the prompt.

You can include more than on tag query in a prompt:

```
resolve lb-radio medium 'tag:(downtempo, trip hop)::or tag:(punk, ska)'
```

#### Stats, Collections, Playlists and Rec

There are more elements, but these are "global" elements that will need to 
have their results resolved to the local collection. The resolution process is
always a bit tricky since its outcome heavily depends on the collection. The
generator will do its best to generate a fitting playlist, but that doesn't
always happen. 

For the other elements, please refer to the 
[ListenBrainz Radio Docs](https://troi.readthedocs.io/en/latest/lb_radio.html)

### Other features

#### Collection deduplication

The `duplicates` command will print a report of duplicate recordings
in your collection, based on MusicBrainz Recording MBIDs. There are several
types of duplicates that this may find:

1. Duplicated tracks with the same title, release and artist.
2. Duplicated tracks that live on different releases, but have the same name
3. Duplicated tracks that exist once on an album and again on a compilation.

If you specify `-e` or `--exclude-different-release`, then case #3 will not be shown.

```
troi db duplicates
```

#### Top tags

The `top-tags` command will print the top tags and the number of times they
have been used in your collection. This requires that the `metadata`
command was run before.

```
troi db metadata
troi db top-tags
```

#### Unresolved Releases

Any tracks that fail to resolve to a local collection will have their
recording_mbid saved in the database. This enables the unresolved releases
report which specifies a list of releases that you might consider adding to your
collection, because in the past they failed to resolve to your location collection.

```
troi db unresolved
```

## Running tests

```
troi test
troi test -v
troi test -v <file to test>
```

## Building Documentation

To build the documentation locally:

    pip install .[docs]
    cd docs
    make clean html
