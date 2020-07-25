#!/bin/bash

if [ "$1" = "build" ]
then
    docker build -f Dockerfile -t metabrainz:troi-sandbox .
    exit
fi

if [ "$1" = "up" ]
then
    docker run -d --rm --name troi-sandbox -v `pwd`:/code/troi metabrainz:troi-sandbox python3 docker/endless.py
    exit
fi

if [ "$1" = "down" ]
then
    docker rm -f troi-sandbox
    exit
fi

docker exec -it troi-sandbox python3 $@
if [ "$?" -eq 137 ]; then
    echo "Error: docker container failed. Out of ram?"
    exit
fi
