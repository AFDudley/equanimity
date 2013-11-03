"""
world.py

Created by AFD on 2013-08-05.
Copyright (c) 2013 A. Frederick Dudley. All rights reserved.
"""
#ZODB needs to log stuff
# TODO -- configure logging separately
import logging
logging.basicConfig()


def get_world(world):
    """ Returns the world by id if provided """
    if isinstance(world, World):
        return world
    else:
        return World.get(world)


import transaction
from persistent import Persistent
from collections import defaultdict
from frozendict import frozendict
from BTrees.OOBTree import OOBTree
from BTrees.IOBTree import IOBTree
from player import Player, WorldPlayer
from clock import WorldClock
from const import WORLD_UID
from db import AutoID
from server import db


def init_db(reset=False, verbose=False, grid_radius=8, square_grid=False):
    """ Creates top level datastructures in the ZODB """
    from grid import Grid, SquareGrid

    if square_grid:
        grid = lambda: SquareGrid(radius=grid_radius)
    else:
        grid = lambda: Grid(radius=grid_radius)
    start = dict(player_uid=lambda: AutoID('player'),
                 # maps uid (int) -> Player
                 players=lambda: IOBTree(),
                 # maps username (str) -> Player
                 player_username=lambda: OOBTree(),
                 # maps email (str) -> Player
                 player_email=lambda: OOBTree(),
                 unit_uid=lambda: AutoID('unit'),
                 units=lambda: IOBTree(),
                 world_uid=lambda: AutoID('world'),
                 worlds=lambda: IOBTree(),
                 rate_limit=lambda: defaultdict(AutoID),
                 weapons=lambda: IOBTree(),
                 grid=grid)

    for k, v in start.iteritems():
        if reset:
            db[k] = v()
        else:
            if k not in db:
                db[k] = v()
        if verbose:
            print k, db[k]
    transaction.commit()


class World(Persistent):

    @classmethod
    def get(self, uid):
        return db['worlds'].get(uid)

    @classmethod
    def create(cls, **kwargs):
        w = World(**kwargs)
        w.persist()
        return w

    def __init__(self, version=0.0, create_fields=True):
        self.players = {}
        self.player = self._get_or_create_world_player()
        self.player.persist()
        self.add_player(self.player)
        self.uid = db['world_uid'].get_next_id()
        self.version = version
        self.clock = WorldClock(self)
        self.fields = frozendict()
        if create_fields:
            self._create_fields()

    def persist(self):
        """ Saves the world to the ZODB """
        db['worlds'][self.uid] = self

    def add_player(self, p):
        """ Adds a player as a participant of this world """
        self.players[p.uid] = p

    def has_player(self, p):
        if hasattr(p, 'uid'):
            if not isinstance(p, Player):
                raise ValueError('Not a player')
            p = p.uid
        return p in self.players

    def award_field(self, new_owner, coords):
        """Transfers a field from one owner to another."""
        if not self.has_player(new_owner):
            raise ValueError('Not participating')
        self.fields[coords].owner = new_owner

    def _get_or_create_world_player(self):
        return db['players'].setdefault(WORLD_UID, WorldPlayer())

    def _create_fields(self):
        """ Creates all fields used in a game. """
        from field import Field
        self.radius = db['grid'].radius
        fields = {}
        for coord in db['grid'].iter_coords():
            fields[coord] = Field(self, coord, owner=self.player)
        self.fields = frozendict(fields)
