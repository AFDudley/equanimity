"""
world.py

Created by AFD on 2013-08-05.
Copyright (c) 2013 A. Frederick Dudley. All rights reserved.
"""
from datetime import datetime

import transaction
import persistent
#ZODB needs to log stuff
import logging
logging.basicConfig()

from const import WORLD_UID
from field import Field
from player import WorldPlayer
from server import db

class World(object):

    def __init__(self):
        self.player = db['player'].get(WORLD_UID)

    def create(self, version=0.0, x=2, y=2):
        # If the world version is the same, do nothing.
        if 'version' in db and db['version'] == version:
            return
        self.setup(version, x, y)
        self.make_fields(db['x'], db['y'])

    def setup(self, version, x, y):
        db['dayLength'] = 240     # length of game day in seconds.
        db['resigntime'] = 21600  # amount of time in seconds before
                                  # attacker is forced to resign.
        db['maxduration'] = 5040  # in gametime days (5040 is one
                                  # generation, two weeks real-time)
        db['version'] = version
        db['x'] = x
        db['y'] = y
        db['DOB'] = datetime.utcnow()
        # fields should be a frozendict
        # http://stackoverflow.com/questions/2703599/what-would-be-a-frozen-dict
        db['fields'] = persistent.mapping.PersistentMapping()
        self.player = db['player'].setdefault(WORLD_UID, WorldPlayer())
        return transaction.commit()

    def make_fields(self, range_x, range_y):
        """creates all fields used in a game."""
        # right now the World and the fields are square,
        # they should both be hexagons.
        wf0 = self.player.fields
        wf1 = db['fields']
        for coord_x in xrange(range_x):
            for coord_y in xrange(range_y):
                world_coord = (coord_x, coord_y)
                f = Field(world_coord)
                wf0[str(world_coord)] = f
                wf1[str(world_coord)] = f
                transaction.commit()

    def award_field(self, old_owner, field_coords, new_owner):
        """Transfers a field from one owner to another."""
        # is this atomic? No, not without a lock
        p = db['player']
        c = str(field_coords)
        p[new_owner.uid].fields[c] = p[old_owner.uid].fields[c]
        del p[old_owner.uid].fields[c]
        p[new_owner.uid].fields[c].owner = new_owner
        return transaction.commit()

    def move_squad(self, src, squad_num, dest):
        """Moves a squad from a stronghold to a queue."""
        #src and dest are both fields
        #TODO: check for adjacency.
        squad = src.stronghold.squads[squad_num]
        dest.attackerqueue.append((src.owner, squad))
        src.stronghold.remove_squad(squad_num)
        return transaction.commit()

    def process_action(self, action):
        # TODO
        pass
