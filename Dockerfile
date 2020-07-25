FROM ubuntu:18.04

RUN apt-get update && apt-get install -y python3-pip python3-setuptools

RUN mkdir -p /code/troi
WORKDIR /code/troi

COPY requirements.txt .
RUN pip3 install -r requirements.txt
