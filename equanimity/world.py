"""
world.py

Created by AFD on 2013-08-05.
Copyright (c) 2013 A. Frederick Dudley. All rights reserved.
"""
#ZODB needs to log stuff
# TODO -- configure logging separately
import logging
logging.basicConfig()

import itertools
import transaction
import persistent
from BTrees.OOBTree import OOBTree
from BTrees.IOBTree import IOBTree

from collections import defaultdict
from datetime import datetime
from threading import Lock

from const import WORLD_UID
from field import Field
from player import WorldPlayer
from server import db
from db import AutoID


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
        self.transfer_lock = Lock()
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

    def create(self, version=0.0, radius=3, init_db_reset=True):
        # If the world version is the same, do nothing.
        if db.get('version') != version:
            self.erase()
            self._setup(version, radius, init_db_reset=init_db_reset)
            self._make_fields()
            #transaction.commit()

    def _setup(self, version, radius, init_db_reset=True):
        db['day_length'] = 240     # length of game day in seconds.
        db['resign_time'] = 21600  # amount of time in seconds before
                                   # attacker is forced to resign.
        db['max_duration'] = 5040  # in gametime days (5040 is one
                                   # generation, two weeks real-time)
        db['version'] = version
        db['radius'] = radius
        db['dob'] = datetime.utcnow()
        #fields should be a frozendict
        #http://stackoverflow.com/questions/2703599/what-would-be-a-frozen-dict
        db['fields'] = persistent.mapping.PersistentMapping()
        db['grid'] = Grid(radius=radius)
        init_db(reset=init_db_reset)
        self.player = db['players'].setdefault(WORLD_UID, WorldPlayer())
        self.player.persist()

    def _make_fields(self, x, y):
        """creates all fields used in a game."""
        # right now the World and the fields are square,
        # they should both be hexagons.
        # TODO (steve) -- generate hexagonal field
        for coord in db['world_grid'].iter_coords():
            f = Field(coord, owner=self.player)
            db['fields'][coord] = f
            self.player.fields[coord] = f

    def award_field(self, new_owner, coords):
        """Transfers a field from one owner to another."""
        # Do the transfer atomically
        field = db['fields'][coords]
        with self.transfer_lock:
            field.owner = new_owner
        transaction.commit()

    def move_squad(self, src, squad_num, dest):
        """Moves a squad from a stronghold to a queue."""
        #src and dest are both fields
        #TODO: check for adjacency.
        # Do the transfer atomically
        with self.transfer_lock:
            squad = src.stronghold.squads[squad_num]
            dest.attackerqueue.append((src.owner, squad))
            src.stronghold.remove_squad(squad_num)
        transaction.commit()
