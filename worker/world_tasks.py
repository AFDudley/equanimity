import sys
import transaction
from equanimity.clock import WorldClock
from server import db, create_app
from celery import Celery
import config
celery = Celery(broker='redis://localhost:6379/0')
celery.conf.update(
    CELERY_BROKER_URL='redis://localhost:6379/0',
    CELERY_RESULT_BACKEND='redis://localhost:6379/0'
)

from redis import Redis, ConnectionPool
r = Redis(connection_pool=ConnectionPool(host='localhost', port=6379, db=1))

@celery.task()
def start_task(world_id):
    """ Starts the game """
    print "Starting World..."
    app = create_app(config='production')
    with app.test_request_context():
        world = db['worlds'].get(world_id)
        if world.clock == None:
            if not world.has_fields:
                world.create_fields()
                world.has_fields = True
            world._distribute_fields_to_players()
            world._populate_fields()
            world.clock = WorldClock()
            uids = world.players.players.keys()
            world.persist()
            app.do_teardown_request()
            for uid in uids:
                print 'user.{}.worlds'.format(uid)
                r.publish('user.{}.worlds'.format(uid), "World {0} persisted.".format(world_id))
            print "World {0} persisted.".format(world_id)
        else:
            raise ValueError("World already started.")
    print "World Start Task Completed."
