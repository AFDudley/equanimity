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

#restart worker
if [ -f celeryd.pid ]; then
    kill $(cat celeryd.pid)
fi

./celery -A worker.world_tasks worker --detach

#restart server
./run_wsgi_server.sh