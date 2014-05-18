#!/usr/bin/env bash

#source /home/rdn/venv/bin/activate

uwsgi --offload-threads 2 --processes 2 --gevent 2 --thunder-lock --http :5000 --virtualenv $VIRTUAL_ENV --module server.wsgi:application

