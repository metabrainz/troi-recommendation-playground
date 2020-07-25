# Introduction

This project is aim to create a sandbox for developers to develop and 
experiment with music recommendation engines. To accomlish this goal,
the MetaBrainz Foundation has created and hosted a number of data-sets
that can be accessed as part of this project.

You can see some of the data sets that are hosted here:

  http://bono.metabrainz.org:8000

The AcousticBrainz project hosts the Annoy indexes that allows 
you to find recordings that have similar characteristics given a
in initial recording.

The ListenBrainz project offers a number of data sets:

1. Collaborative filtered recordings that suggest what recordings a 
user should listen to based on their previous listening habits.
2. User statistics that were derived from users recent listening
habits.

MusicBrainz provides:

1. Related artists -- which artists are related to other artists.

MessyBrainz provides:

1. MessyBrainz -> MusicBrain mapping for mapping listens with MSIDs
   to MusicBrainz MBIDs


## installation


**Linux and Mac**
```
virtualenv -p python3 .ve
source .ve/bin/activate
pip3 install -r requirements.txt
```

If you plan to do local development or run tests, you'll need to:

```
pip3 install -e .
```

**Windows**

```
virtualenv -p python3 .ve
.ve\Scripts\activate.bat
pip3 install -r requirements.txt
```

**Docker**

On non Linux operating systems installing python modules can be a bit of a pain. For that a thin-shell docker
container can be created. Note that docker is not required, but helpful if you're not on Linux.

To use this container, you first need to build the container and start it:

```
./run-docker.sh build
./run-docker.sh up
```

Now you can run any of the scripts via run-docker.sh:

```
./run-docker.sh recommend_recordings.py rob similar
```

When you are done with the container, take it down with:

```
./run-docker.sh up
```

To run tests:

```
./run-docker.sh test
```


## sample use

**Linux**
```
./recommended_recordings.py <user name>
open OpenPost.html
```

**Windows**
```
python recommended_recordings.py <user name>
OpenPost.html
```

**Docker**

If you installed the system via docker, you can run scripts via:

```
./run-docker.sh recommend_recordings.py rob similar
open OpenPost.html
```
