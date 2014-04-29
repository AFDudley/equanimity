#!/bin/bash

sudo service uwsgi stop

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

#restart worker
#if [ -f celeryd.pid ]; then
#    kill $(cat celeryd.pid)
#fi

#./celery -A worker.world_tasks worker --detach

#restart server
#./run_wsgi_server.sh
sudo service uwsgi start

