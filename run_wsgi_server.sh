#!/usr/bin/env bash

source /home/rdn/venv/bin/activate

uwsgi --http :8080 --virtualenv /home/rdn/venv/ --module server.wsgi:application
