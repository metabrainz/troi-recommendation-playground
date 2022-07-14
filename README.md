# Introduction

This project is aim to create a sandbox for developers to develop and
experiment with music recommendation engines. To accomplish this goal,
the MetaBrainz Foundation has created and hosted a number of data-sets
that can be accessed as a part of this project.

The project is named after [Deanna Troi](https://en.wikipedia.org/wiki/Deanna_Troi).

The AcousticBrainz project hosts the Annoy indexes that allows
you to find recordings that have similar characteristics given an initial recording.

The ListenBrainz project offers a number of data sets:

1. Collaborative filtered recordings that suggest what recordings a
user should listen to based on their previous listening habits.
2. User statistics that were derived from users recent listening
habits.

MusicBrainz provides:

1. Related artists -- which artists are related to other artists.

MessyBrainz provides:

1. MessyBrainz -> MusicBrainz mapping for mapping listens with MSIDs
   to MusicBrainz MBIDs


## Installation for end users

TBC -- waiting for modules to be shipped to pypi.

## Installation for Development

**Linux and Mac**

```
virtualenv -p python3 .ve
source .ve/bin/activate
pip3 install -r requirements.txt
python3 -m troi.cli --help
```

**Windows**

```
virtualenv -p python .ve
.ve\Scripts\activate.bat
pip install -r requirements.txt
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

## References for the future path of Troi

Troi is a rather primitive tool at this point in time, but as the MetaBrainz projects gather more data, we can improve
how we generate playlists. A good overview of the technology and psychology behind playlists and recommendations, see:

* https://www.slideshare.net/BenFields/finding-a-path-through-the-juke-box-the-playlist-tutorial?utm_source=pocket_mylist


