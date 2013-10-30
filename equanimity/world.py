"""
world.py

Created by AFD on 2013-08-05.
Copyright (c) 2013 A. Frederick Dudley. All rights reserved.
"""
#ZODB needs to log stuff
# TODO -- configure logging separately
import logging
logging.basicConfig()

import transaction
from collections import defaultdict
from threading import Lock
from persistent.mapping import PersistentMapping
from BTrees.OOBTree import OOBTree
from BTrees.IOBTree import IOBTree

from const import WORLD_UID
from field import Field
from player import WorldPlayer
from db import AutoID
from grid import Grid, SquareGrid
from clock import WorldClock
from server import db


def init_db(reset=False, verbose=False):
    start = dict(player_uid=AutoID('player'),
                 players=IOBTree(),           # maps uid (int) -> Player
                 player_username=OOBTree(),  # maps username (str) -> Player
                 player_email=OOBTree(),     # maps email (str) -> Player
                 unit_uid=AutoID('unit'),
                 units=IOBTree(),
                 rate_limit=defaultdict(AutoID),
                 weapons=IOBTree())
    for k, v in start.iteritems():
        if reset:
            db[k] = v
        else:
            db.setdefault(k, v)
        if verbose:
            print k, db[k]
    transaction.commit()


class World(object):
    def __init__(self):
        self.lock = Lock()
        self.player = None

    @classmethod
    def erase(cls):
        keys = ['day_length', 'resign_time', 'max_duration', 'version', 'x',
                'y', 'dob', 'fields']
        for key in keys:
            if key in db:
                del db[key]
        for player in db.get('players', {}).itervalues():
            player.reset_world_state()

    def create(self, version=0.0, radius=8, square_grid=False,
               init_db_reset=True):
        # If the world version is the same, do nothing.
        if db.get('version') != version:
            self.erase()
            self._setup(version, radius, square_grid=square_grid,
                        init_db_reset=init_db_reset)
            self._make_fields()

    def _setup(self, version, radius, square_grid=False, init_db_reset=True):
        db['version'] = version
        db['radius'] = radius
        db['clock'] = WorldClock()
        #fields should be a frozendict
        #http://stackoverflow.com/questions/2703599/what-would-be-a-frozen-dict
        db['fields'] = PersistentMapping()
        if square_grid:
            db['grid'] = SquareGrid(radius=radius)
        else:
            db['grid'] = Grid(radius=radius)
        init_db(reset=init_db_reset)
        self.player = db['players'].setdefault(WORLD_UID, WorldPlayer())
        self.player.persist()

    def _make_fields(self):
        """creates all fields used in a game."""
        # right now the World and the fields are square,
        # they should both be hexagons.
        # TODO (steve) -- generate hexagonal field
        for coord in db['grid'].iter_coords():
            f = Field(coord, owner=self.player)
            db['fields'][coord] = f
            self.player.fields[coord] = f

    def award_field(self, new_owner, coords):
        """Transfers a field from one owner to another."""
        with self.lock:
            db['fields'][coords].owner = new_owner
