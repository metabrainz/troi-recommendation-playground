FROM tiangolo/uwsgi-nginx-flask:python3.8

RUN apt-get update && apt-get install -y ca-certificates
RUN python3 -m pip install --upgrade pip

COPY requirements.txt /tmp
RUN python3 -m pip install -r /tmp/requirements.txt

RUN mkdir -p /app/troi /app/troi/template
WORKDIR /app/troi
COPY . /app

COPY troi/webserver/main.py /app
RUN chmod +x /app/main.py
COPY troi/webserver/template/* /app/template/
