# Introduction

This project aims to create an open source music recommendation toolkit with an API-first
philiosophy. API-first means that user do no need to download a lot of data before they
can start working with Troi -- all the needed data should ideally live in online APIs, making
it very easy for someone to get started hacking on music recommendations.

To accomplish this goal, we, the MetaBrainz Foundation, have created and hosted a number of data-sets
that can be accessed as a part of this project. For instance, the more stable APIs are hosted on our
Labs API page](https://labs.api.listenbrainz.org).

The ListenBrainz project offers a number of data sets:

1. Collaborative filtered recordings that suggest what recordings a user should listen to based on
their previous listening habits.
2. User statistics that were derived from users recent listening habits.

We will continue to build and host more datasets as time passes. If an API endpoint becomes useful to
a greater number of people we will elevate these API endpoints to officially supported endpoints
that we ensure are up to date on online at all times.

The project is named after [Deanna Troi](https://en.wikipedia.org/wiki/Deanna_Troi).

# Documentation

Full documentation for Troi is available at [troi.readthedocs.org](https://troi.readthedocs.org).

# Technical Introduction

Troi uses a pipeline architecture comprised of Elements (a node in the pipeline) that can be chained
togther. Each element can be a source of data and act like a filter that takes the incoming data,
acts on it and passes output data. At the end of the pipeline, the last element should return
a Playlist object that the Troi main function can then display or submit to ListenBrainz or other
services.

A pipeline, and the Elements that it is composed of are called a Patch. The most common data passed
through a data are Recording objects that represent a MusicBrainz recording. But other data elements
such as Users, Artists and Releases could easily be objects passed through a pipeline. A patch never
processes data on its own -- a Patch returns a constructed pipeline of Elements that are chained 
together. The Elements are the classes that process data, but those are invoked only after the pipeline
is constructed and when Troi begins to generate a playlist.

If is not uncommon to have a PlaylistRedundancyReducerElement at the end of the pipeline
which returns a Playlist object of the desired length with a limit to the number of times a single
artist's tracks can be included in the playlist.

The pre-defined elements User, Artist, Release, Recording all have elements of MBID and name. A recording
also had an Artist element included for obvious reasons. The Artist element actually contains support
for more than one artist, so its MBID element is actually plural MBIDS in order to accurately represent
a MusicBrainz Artist Credit. Each of these objects contains two free form dicts: musicbrainz and listenbrainz.
When you fetch data that doesn't fit into the predefined fields of the data object classes, that data can be
stored in these free form dicts. For instance, a Recording element that was loaded from ListenBrainz
statistics will have a listen_count field.


# Current Patches

We have a few patches that ship with Troi:

# Area Random Recordings

Given a geograpic area (defined in terms of an area in MusicBrainz) and start/end year, choose random tracks
from this given country and return a playlist of these tracks.



## Installation for end users

So far we've not uploaded Troi bundles to PyPi -- please use the installation instructions for developers
below.

## Installation for Development

**Linux and Mac**

```
virtualenv -p python3 .ve
source .ve/bin/activate
pip3 install -r requirements.txt -r requirements_test.txt
python3 -m troi.cli --help
```

**Windows**

```
virtualenv -p python .ve
.ve\Scripts\activate.bat
pip install -r requirements.txt -r requirements_test.txt
python -m troi.cli --help
```

## Basic commands

List available patches:

    python -m troi.cli list

Generate a playlist using a patch:

    python -m troi.cli playlist --print [patch-name]

If the patch requires arguments, running it with no arguments will print a usage statement, e.g.

    $ python -m troi.cli playlist --print area-random-recordings
    Usage: area-random-recordings [OPTIONS] AREA START_YEAR END_YEAR
   
      Generate a list of random recordings from a given area.
   
      AREA is a MusicBrainz area from which to choose tracks.
      START_YEAR is the start year.
      END_YEAR is the end year.
   
    Options:
      --help  Show this message and exit.

## Running tests

```
python3 -m troi.cli test
python3 -m troi.cli test -v
python3 -m troi.cli test -v <file to test>
```

## Building Documentation

To build the documentation locally:

    cd docs
    pip install -r requirements.txt
    make clean html

## References for the future path of Troi

Troi is a rather primitive tool at this point in time, but as the MetaBrainz projects gather more data, we can improve
how we generate playlists. A good overview of the technology and psychology behind playlists and recommendations, see:

* https://www.slideshare.net/BenFields/finding-a-path-through-the-juke-box-the-playlist-tutorial?utm_source=pocket_mylist
