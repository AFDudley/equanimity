#!/usr/bin/env bash

#source /home/rdn/venv/bin/activate

uwsgi --http :8080 --virtualenv $VIRTUAL_ENV --module server.wsgi:application
