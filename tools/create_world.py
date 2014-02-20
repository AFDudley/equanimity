#!/usr/bin/env python
"""creates the World object and populates it with fields. VERY DESTRUCTIVE."""
from common import hack_syspath
hack_syspath(__file__)

from equanimity.world import World
from server import create_app


def create_world():
    w = World.create()
    w.start()
    w.persist()


if __name__ == '__main__':
    with create_app().test_request_context():
        create_world()
