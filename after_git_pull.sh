#!/bin/bash

sudo service uwsgi stop

#remove old pyc files
find . -type f -name '*.pyc' | xargs rm

# clean up zodb
sudo pkill -f runzeo
sudo rm /var/www/zeo/world/*
sudo runzeo -C zeo/zeoAWS.conf &
sleep 3

# write commit number to file
sudo su -c "git log --format=%h -n 1 > gitinfo.txt" -s /bin/sh www-data
sudo su -c "git rev-parse --abbrev-ref HEAD >> gitinfo.txt" -s /bin/sh www-data

#create new db
tools/init_db.py

#restart server
sudo service uwsgi start

