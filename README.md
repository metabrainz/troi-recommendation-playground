# Introduction

This project is aim to create a sandbox for developers to develop and
experiment with music recommendation engines. To accomplish this goal,
the MetaBrainz Foundation has created and hosted a number of data-sets
that can be accessed as a part of this project.

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
virtualenv -p python3 .ve
.ve\Scripts\activate.bat
pip3 install -r requirements.txt
python3 -m troi.cli --help
```

## Running tests

```
python3 -m troi.cli test
python3 -m troi.cli test -v
python3 -m troi.cli test -v <file to test>
```

## hosting troi on the web with docker

To run a container with the build-in webserver, do:

```
docker build -t metabrainz/troi-hoster .
docker run --rm -p 8000:80 --name troi-hoster metabrainz/troi-hoster
```
