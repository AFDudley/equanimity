#!/usr/bin/env bash
uwsgi --http :8080 --virtualenv $VIRTUAL_ENV --module server.wsgi:application

