FROM python:3.8.5-buster

#RUN apt-get update && apt-get install -y python3-pip \
#        python3-setuptools \ 
#        python3-virtualenv

ENV VIRTUAL_ENV=/opt/venv
RUN python3 -m venv $VIRTUAL_ENV
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

RUN mkdir -p /code/troi
WORKDIR /code/troi

COPY requirements.txt setup.py ./
RUN pip3 install -r requirements.txt
RUN pip3 install -e .
