# Introduction

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

The project is named after [Deanna Troi](https://en.wikipedia.org/wiki/Deanna_Troi).

## Features

### Playlist generation

Troi can be used to generate playlists:

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
local collection. This is optimized for local collections and gives better results than
the global troi patch by the same name.

3. Resolve global playlists (usually JSPF files with MusicBrainz IDs) to a local collection
of music. Resolution happens via: MusicBrainz IDs, metadata matching or fuzzy metadata matching.

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

```
virtualenv -p python3 .ve
pip3 install troi[nmslib]
troi --help
```

Troi also depends on [nmslib-metabrainz](https://github.com/metabrainz/nmslib-metabrainz)
to enable fuzzy matching of tracks against a local collection. nmslib-metabrainz is not
required to run troi, it's only required for fuzzy matching, so if you're having a hard
time installing nsmlib, omit it like this:

```
virtualenv -p python3 .ve
pip3 install troi
troi --help
```

### Installation for Development

Note: If you have trouble installing nmslib, it is optional. Remove nsmlib from the install command below:

**Linux and Mac**

```
virtualenv -p python3 .ve
source .ve/bin/activate
pip3 install -e .[nmslib,tests]
troi --help
```

**Windows**

```
virtualenv -p python .ve
.ve\Scripts\activate.bat
pip install -e .[nmslib,tests]
troi --help
```

## User-guide

For details on how to run Troi, please see [see our user guide](https://troi.readthedocs.io/en/latest/user-guide.html).

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
