import os
import sys
import signal
from datetime import datetime
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

celery = Celery(broker='redis://localhost:6379/0')
celery.conf.update(
    CELERY_BROKER_URL='redis://localhost:6379/0',
    CELERY_RESULT_BACKEND='redis://localhost:6379/0',
    CELERY_DISABLE_RATE_LIMITS = True,
    CELERYBEAT_SCHEDULE = {} #  TODO put tick tock on the scheduler
)

from redis import Redis, ConnectionPool
r = Redis(connection_pool=ConnectionPool(host='localhost', port=6379, db=1))

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
            print "Waiting .25 seconds for ZODB."
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
            for uid in uids:
                print 'user.{}.worlds'.format(uid)
                event = json.dumps(dict(world=dict(uid=world_id,
                                        event="persisted",
                                        when=when)))
                r.publish('user.{}.worlds'.format(uid), event)
            print event
        else:
            raise ValueError("World already started.")
    print "World Start Task Completed."
    return tick_tock.delay(world_id)

@celery.task(name='world_tasks.tick_tock', ignore_result=True)
def tick_tock(world_id):
    """Takes a world ID and advances the clock of that world"""
    global app_n
    os.setsid()
    signal.signal(signal.SIGTERM, sigterm_handler)
    while True:
        gevent.sleep(CLOCK['day'].seconds)
        print "Tick for World {0} started at: {1}".format(world_id, datetime.utcnow())
        with app_n.test_request_context():
            db.connection.sync()
            world = db['worlds'].get(world_id)
            world.clock.tick(world.fields)
            world.persist()
            app_n.do_teardown_request()
            db.connection.close()
        print "Tick for World {0} ended at: {1}".format(world_id, datetime.utcnow())

