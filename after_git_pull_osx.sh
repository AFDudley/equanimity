#!/bin/bash

pkill uwsgi

#remove old pyc files
find . -type f -name '*.pyc' | xargs rm

# clean up zodb
pkill -f runzeo
rm DBs/world/*
runzeo -C zeo/zeoWorld.conf &

#create new db
tools/init_db.py

#restart server
./run_wsgi_server.sh