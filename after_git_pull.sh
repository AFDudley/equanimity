#!/bin/bash

sudo service uwsgi stop
sudo service celeryd stop

#remove old pyc files
find . -type f -name '*.pyc' | xargs rm

# clean up zodb
sudo pkill -9f runzeo
rm ~/DBs/world/*
runzeo -C zeo/zeoDO.conf &

#create new db
tools/init_db.py

# write commit number to file
git log --format=%h -n 1 > gitinfo.txt
git rev-parse --abbrev-ref HEAD >> gitinfo.txt

#restart server
sudo service celeryd start
sudo service uwsgi start

