#!/usr/bin/env bash

#source /home/rdn/venv/bin/activate

uwsgi --processes 50 --gevent 3 --http :5000 --virtualenv $VIRTUAL_ENV --module server.wsgi:application

