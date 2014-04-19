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

@celery.task()
def start_task(world_id):
    """ Starts the game """
    print "Starting World..."
    with create_app(config='production').test_request_context():
        world = db['worlds'].get(world_id)
        if world.clock == None:
            if not world.has_fields:
                world.create_fields()
                world.has_fields = True
            world._distribute_fields_to_players()
            world._populate_fields()
            world.clock = WorldClock()
            world.persist()
            print "World {0} persisted.".format(world_id)
        else:
            raise ValueError("World already started.")