#!/usr/bin/env bash
uwsgi --offload-threads 2 --processes 2 --gevent 2 --thunder-lock --http :8080 --virtualenv $VIRTUAL_ENV --module server.wsgi:application
