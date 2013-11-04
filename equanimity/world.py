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
from random import choice, randrange
from player import Player, WorldPlayer
from clock import WorldClock
from const import WORLD_UID, ELEMENTS, ORTH
from stone import Stone, Composition
from grid import Grid, SquareGrid
from db import AutoID
from server import db


def init_db(reset=False, verbose=False, grid_radius=8, square_grid=False):
    """ Creates top level datastructures in the ZODB """

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
        self.radius = db['grid'].radius
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

    def _choose_initial_field_element(self, coord):
        """ Decide what element to assign a field based on coordinate """
        # For now, just choose a random element. Later, distribute the
        # elements by a heuristic
        return choice(ELEMENTS)

    def _choose_initial_field_grid(self, element, coord):
        """Decide what stones to populate a grid's tiles with and return
        the grid
        """
        c = Composition()
        c[element] = randrange(20, 40)
        c.set_opp(element, randrange(5, 10))
        for x in ORTH[element]:
            c[x] = randrange(10, 20)
        return Grid(comp=Stone(c), radius=self.radius)

    def _create_fields(self):
        """ Creates all fields used in a game. """
        from field import Field
        fields = {}
        for coord in db['grid'].iter_coords():
            """
            Field need to be given:
              An element
              Grid needs to filled with values based on a target value,
                  and the field's element
              Fully equipped squad in stronghold
                  (NO, do this when assigning to a player, after game is
                   started)
            """
            e = self._choose_initial_field_element(coord)
            grid = self._choose_initial_field_grid(e, coord)
            fields[coord] = Field(self, coord, e, owner=self.player, grid=grid)
        self.fields = frozendict(fields)
