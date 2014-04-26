#!/usr/bin/env bash

#source /home/rdn/venv/bin/activate

uwsgi --processes 3 --gevent 5 --http :8080 --virtualenv $VIRTUAL_ENV --module server.wsgi:application

