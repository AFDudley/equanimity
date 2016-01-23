import os
import sys
import signal
from datetime import datetime, timedelta
import transaction
from flask import json
from equanimity.helpers import now
from equanimity.const import CLOCK
from equanimity.clock import WorldClock
from server import db, create_app
from celery import Celery
from celery.task.control import revoke
import config
import gevent

celery = Celery(broker='redis://127.0.0.1:6379/0')
celery.conf.update(
    CELERY_BROKER_URL='redis://127.0.0.1:6379/0',
    CELERY_RESULT_BACKEND='redis://127.0.0.1:6379/0',
    CELERY_DISABLE_RATE_LIMITS = True,
    CELERY_TIMEZONE = 'UTC',
    CELERYBEAT_SCHEDULE = {
        'tick-worlds': {
            'task': 'world_tasks.tick_worlds',
            'schedule': CLOCK['day'] / 2
            #'schedule': timedelta(seconds=.1)
        },
    }
)

from redis import Redis, ConnectionPool
r = Redis(connection_pool=ConnectionPool(host='127.0.0.1', port=6379, db=1))

app_n = None

def sigterm_handler(signum, frame):
    print >>sys.stderr, "SIGTERM handler.  Shutting Down."
    os.killpg(0, signal.SIGTERM)
    sys.exit()


@celery.task(name='world_tasks.start_world', ignore_result=True)
def start_world(world_id):
    """ Starts the game """
    global app_n
    print "Starting World..."
    if app_n == None:
        app_n = create_app(config='production')
    with app_n.test_request_context():
        # zeo load seems to slow down assignment to world variable
        db.connection.sync()
        world = db['worlds'].get(world_id)
        while world == None:
            db.connection.sync()
            world = db['worlds'].get(world_id)
            gevent.sleep(.25)
        if world.clock == None:
            if not world.has_fields:
                world.create_fields()
                world.has_fields = True
            world._distribute_fields_to_players()
            world._populate_fields()
            world.clock = WorldClock()
            uids = world.players.players.keys()
            world.persist()
            app_n.do_teardown_request()
            db.connection.close()
            when = now().isoformat()
            for uid in uids:
                print 'user.{}.worlds'.format(uid)
                event = json.dumps(dict(persisted=dict(uid=world_id,when=when)))
                r.publish('user.{}.worlds'.format(uid), event)
            print event
        else:
            raise ValueError("World already started.")
    print "World Start Task Completed."
    return

@celery.task(name='world_tasks.tick_worlds', ignore_result=True)
def tick_worlds():
    print "Ticking worlds."
    global app_n
    if app_n == None:
        app_n = create_app(config='production')
    with app_n.test_request_context():
        update = False
        for world in db['worlds'].values():
            if world.has_fields:
                print "\tTicking World {}.".format(world.uid)
                update = True
                world.clock.tick(world.fields)
                world.persist()
        if update:
            app_n.do_teardown_request()
            db.connection.close()
    print "Worlds ticked."
    return


@celery.task(name='heartbeat', ignore_result=True)
def heartbeat():
    global app_n
    if app_n == None:
        app_n = create_app(config='production')
    with app_n.test_request_context():
        for player in db['players'].values():
            if player.login_count > 0:
                pid = player.uid
                when = now().isoformat()
                event = json.dumps(dict(ping=dict(uid=0, when=when)))
                r.publish('user.{}.heartbeat'.format(pid), event)
                print "Sent uid {} heartbeat.".format(pid)
        app_n.do_teardown_request()
        db.connection.close()
    return