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
from datetime import datetime
from threading import Lock

from const import WORLD_UID
from field import Field
from player import WorldPlayer
from server import db


class World(object):

    def __init__(self):
        self.field_transfer_lock = Lock()
        self.squad_transfer_lock = Lock()
        self.player = db['player'].get(WORLD_UID)

    @classmethod
    def erase(cls):
        keys = ['day_length', 'resign_time', 'max_duration', 'version', 'x',
                'y', 'dob', 'fields']
        for key in keys:
            if key in db:
                del db[key]
        for player in db.get('player', {}).itervalues():
            player.reset_world_state()
        transaction.commit()

    def create(self, version=0.0, x=2, y=2):
        # If the world version is the same, do nothing.
        if 'version' not in db or db['version'] != version:
            self.erase()
            self._setup(version, x, y)
            self._make_fields(x, y)

    def _setup(self, version, x, y):
        db['day_length'] = 240     # length of game day in seconds.
        db['resign_time'] = 21600  # amount of time in seconds before
                                  # attacker is forced to resign.
        db['max_duration'] = 5040  # in gametime days (5040 is one
                                  # generation, two weeks real-time)
        db['version'] = version
        db['x'] = x
        db['y'] = y
        db['dob'] = datetime.utcnow()
        #fields should be a frozendict
        #http://stackoverflow.com/questions/2703599/what-would-be-a-frozen-dict
        db['fields'] = persistent.mapping.PersistentMapping()
        self.player = db['player'].setdefault(WORLD_UID, WorldPlayer())
        transaction.commit()

    def _make_fields(self, x, y):
        """creates all fields used in a game."""
        # right now the World and the fields are square,
        # they should both be hexagons.
        # TODO (steve) -- generate hexagonal field
        for coord in itertools.product(xrange(x), xrange(y)):
            f = Field(coord)
            self.player.fields[coord] = f
            db['fields'][coord] = f
            transaction.commit()

    def award_field(self, old_owner, field_coords, new_owner):
        """Transfers a field from one owner to another."""
        c = field_coords
        # Do the transfer atomically
        with self.field_transfer_lock:
            new_owner.fields[c] = old_owner.fields[c]
            del old_owner.fields[c]
            new_owner.fields[c].owner = new_owner
        return transaction.commit()

    def move_squad(self, src, squad_num, dest):
        """Moves a squad from a stronghold to a queue."""
        #src and dest are both fields
        #TODO: check for adjacency.
        # Do the transfer atomically
        with self.squad_transfer_lock:
            squad = src.stronghold.squads[squad_num]
            dest.attackerqueue.append((src.owner, squad))
            src.stronghold.remove_squad(squad_num)
        return transaction.commit()

    def process_action(self, action):
        # TODO
        pass
