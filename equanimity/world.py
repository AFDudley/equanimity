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
from collections import defaultdict, OrderedDict
from frozendict import frozendict
from BTrees.OOBTree import OOBTree
from BTrees.IOBTree import IOBTree
from random import choice, randrange, sample, shuffle, randint
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
                 vestibules=lambda: IOBTree(),
                 vestibule_uid=lambda: AutoID('vestibule'),
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

    def __init__(self, version=0.0, create_fields=True, players=None):
        self.players = PlayerGroup()
        self.player = self._get_or_create_world_player()
        self.player.persist()
        self.players.add(self.player)
        self.uid = db['world_uid'].get_next_id()
        self.version = version
        self.clock = WorldClock(self)
        self.grid = db['grid']
        self.fields = frozendict()
        if create_fields:
            self._create_fields()

    def persist(self):
        """ Saves the world to the ZODB """
        db['worlds'][self.uid] = self

    def award_field(self, new_owner, coords):
        """Transfers a field from one owner to another."""
        if not self.players.has(new_owner):
            raise ValueError('Not participating')
        self.fields[coords].owner = new_owner

    def start(self):
        """ Starts the game """
        self._distribute_fields_to_players()

    def _get_or_create_world_player(self):
        return db['players'].setdefault(WORLD_UID, WorldPlayer())

    def _distribute_fields_to_players(self):
        """ Assigns fields to participating players """
        # Setup a player, field_count list
        players = [[p, 0] for p in self.players if p != self.player]
        # Decide how many fields player gets
        each_get = len(self.grid) // len(players)
        # Get the coordinates of the fields, minus any fields not to be
        # assigned to players (at random)
        coords = list(self.grid.iter_coords())
        shuffle(coords)
        coords = coords[:-(len(self.grid) % each_get)]
        while coords:
            for p_i in players:
                p, i = p_i
                if i >= each_get:
                    # This player has all their fields
                    continue
                # Fields should be distributed in clusters of 1-4
                cluster_size = max(randint(0, 3), each_get - i - 1)
                # Get the starting coordinate
                ours = [coords.pop(randrange(len(coords)))]
                # Get random available adjacent coordinates for the cluster
                if cluster_size:
                    adj = self.grid.get_adjacent(ours[0])
                    extra = sample(adj, cluster_size)
                    for x in extra:
                        if x in coords:
                            coords.pop(coords.index(x))
                    ours += extra
                # Assign the fields to this player
                for c in ours:
                    self.award_field(p, c)
                # Update this player's field count
                p_i[1] += len(ours)

    def _populate_fields(self):
        """ Puts scients, nescients into fields based on who owns them.
        To be called only after assigning initial fields to all players,
        and before the game begins.
        """
        for f in self.fields:
            kind = None
            if f.owner != self.player:
                kind = 'Scient'
            f.stronghold.populate(kind=kind)

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
        return Grid(comp=Stone(c), radius=self.grid.radius)

    def _create_fields(self):
        """ Creates all fields used in a game. """
        from field import Field
        fields = {}
        for coord in self.grid.iter_coords():
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


class PlayerGroup(object):
    """ Manager for a group of players """

    def __init__(self):
        self.players = OrderedDict()
        self._leader = None

    def has(self, player):
        if hasattr(player, 'uid'):
            if not isinstance(player, Player):
                raise ValueError('Not a player')
            player = player.uid
        return (player in self.players)

    def add_all(self, players):
        for p in players.players.itervalues():
            self.add(p)

    def add(self, player):
        self.players[player.uid] = player
        if self._leader is None:
            self._leader = player

    def remove(self, player):
        if self.leader == self.players[player.uid]:
            self._leader = None
        del self.players[player.uid]

    def get_leader(self, allow_world=True):
        if not allow_world:
            wp = WorldPlayer.get()
        if self._leader is None:
            players = self.players.values()
            if not allow_world:
                players = [p for p in players if p != wp]
            if self.players:
                return players[0]
        else:
            if not allow_world and self._leader == wp:
                players = [p for p in players if p != wp]
                if players:
                    return players[0]
            else:
                return self._leader

    def __iter__(self):
        return iter(self.players)
