"""
field.py

Created by AFD on 2013-08-05.
Copyright (c) 2013 A. Frederick Dudley. All rights reserved.
"""
import random
from persistent import Persistent
from math import ceil
from collections import OrderedDict

from helpers import atomic
from stone import Stone, get_element
from grid import Grid, Hex
from player import WorldPlayer
from battle import Game
from stronghold import Stronghold
from clock import FieldClock
from unit_container import Squad
from units import Scient
from const import FIELD_BATTLE, I
from server import db


class FieldQueue(Persistent):
    """ Manages requests to move into a field """

    def __init__(self, field):
        self.field = field
        self.flush()

    def flush(self):
        self.queue = OrderedDict()

    def add(self, squad):
        if squad.stronghold is None:
            msg = 'Squad must be in a stronghold to move to a field'
            raise ValueError(msg)
        f = self.field
        sq_pos = squad.stronghold.location
        if not f.grid.is_adjacent(f.world_coord, sq_pos):
            raise ValueError('Fields must be adjacent')
        slot = sq_pos - f.world_coord
        if slot in self.queue:
            raise ValueError('Queue slot is taken')
        self.queue[slot] = squad
        squad.queue_at(self.field)

    def pop(self):
        if not self.queue:
            return
        else:
            s = self.queue.popitem(last=False)[1]
            s.unqueue()
            return s


class Field(Persistent):
    """Player owned field logic."""

    @classmethod
    def get(self, loc):
        return db['fields'].get(tuple(loc))

    def __init__(self, world_coord, owner=None, grid=None):
        self.world_coord = Hex._make(world_coord)
        self._owner = None
        if owner is None:
            owner = WorldPlayer.get()
        self.owner = owner
        if grid is None:
            grid = Grid()
        self.grid = grid
        self.element = I  # For testing (TODO)
        #self.element = get_element(self.grid.comp)
        self.clock = FieldClock(self)
        self.stronghold = Stronghold(self)
        self.queue = FieldQueue(self)
        self.plantings = {}
        self.game = None

    def api_view(self, requester=None):
        if (requester is not None and
                self.world_coord not in requester.visible_fields):
            return {}
        # TODO -- add factory etc stuff
        return dict(owner=self.owner.uid,
                    element=self.element,
                    coordinate=self.world_coord,
                    state=self.state,
                    clock=self.clock.api_view())

    @property
    def in_battle(self):
        return (self.game is not None and not self.game.state['game_over'])

    @property
    def state(self):
        if self.in_battle:
            return FIELD_BATTLE
        else:
            return self.clock.state

    @property
    def owner(self):
        return self._owner

    @owner.setter
    @atomic
    def owner(self, owner):
        if owner == self._owner:
            return
        if self._owner is not None:
            del self._owner.fields[self.world_coord]
        self._owner = owner
        owner.fields[self.world_coord] = self

    @atomic
    def process_queue(self):
        next_squad = self.queue.pop()
        if next_squad is not None:
            if next_squad.owner == self.owner:
                self.stronghold.move_squad_in(next_squad)
            else:
                self.start_battle(next_squad)
        return next_squad

    def start_battle(self, attacking_squad):
        self.game = Game(self, attacking_squad)
        self.game.start()

    def place_scient(self, unit, location):
        if unit.__class__ != Scient:
            raise ValueError('Unit {0} must be a scient'.format(unit))
        location = Hex._make(location)
        # Placement can only be on one side of the field
        if location[0] <= 0:
            raise ValueError('First coordinate of location must be positive')
        # Unit must be in a squad
        if not isinstance(unit.container, Squad):
            raise ValueError('Unit must be in a squad to be placed on a field')
        # Location must fit on grid
        if not self.grid.in_bounds(location):
            msg = 'Location {0} does not fit on the field'
            raise ValueError(msg.format(location))
        # Unit must not collide with other units placed in its squad
        for u in unit.container:
            if u != unit and u.chosen_location == location:
                msg = 'Location is already occupied by squad member {0}'
                raise ValueError(msg.format(u))
        unit.chosen_location = location

    def rand_place_scient(self, unit):
        """Randomly place a unit on the grid."""
        available = set(self.grid.placement_coords())
        if not available:
            raise ValueError("Grid is full")
        taken = set([u.chosen_location for u in unit.container
                     if not u.chosen_location.is_null()])
        available = available - taken
        return self.place_scient(unit, random.choice(available))

    def rand_place_squad(self, squad):
        """place the units in a squad randomly on the battlefield"""
        # Clear any previously chosen locations
        for u in squad:
            u.chosen_location = Hex.null
        available = set(self.grid.placement_coords())
        positions = random.sample(available, len(squad))
        for unit, pos in zip(squad, positions):
            self.place_scient(unit, pos)

    def set_stronghold_capacity(self):
        """Uses grid.value to determine stronghold capacity."""
        # squad points. scient = 1 nescient = 2
        # capacity increases at:
        # [61, 125, 189, 253, 317, 381, 445, 509, 573, 637, 701, 765, 829,
        #  893, 957,]
        spaces = ceil((self.grid.value() + 4) / 64.0)
        self.stronghold.units.free_spaces = int(spaces) * 8

    def get_tile_comps(self):
        """returns a list of stones 1/8th the value of the tile comps."""
        stone_list = []
        for tile in self.grid.iter_tiles():
            stone = Stone()
            for suit, value in tile.comp.iteritems():
                stone[suit] += value / 8  # this 8 will need to be tweaked.
            if stone.value() != 0:
                stone_list += [stone]
        return stone_list

    def set_silo_limit(self):
        """Sets the silo limit to 1 year's worth of stones."""
        #this uses get_tile_comps so the / 8 is only maintained in one place.
        limit = {'Earth': 0, 'Fire': 0, 'Ice': 0, 'Wind': 0}
        for stone in self.get_tile_comps():
            for element in limit.keys():
                limit[element] += stone[element]
        return self.stronghold.silo.set_limit(limit)

    def add_planting(self, loc, comp):
        self.planting[loc] = comp, sum(comp.values())

    def plant(self):
        """Plants from self.plantlings"""
        if self.stronghold.farm.produce(self.plantings):
            for loc, comp in self.plantings.iteritems():
                stone = self.stronghold.silo.get(comp)
                self.grid.imbue_tile(loc, stone)
                self.grid.get(loc)._p_changed = 1
                self.grid._p_changed = 1
                self.element = get_element(self.grid.comp)
                self._p_changed = 1
                self.set_stronghold_capacity()
                self.set_silo_limit()

    def harvest(self):
        """returns set of stones generated at harvest"""
        #this needs to be more clever and relate to the units in
        #the stronghold somehow.
        #happens once a year.
        return self.stronghold.silo.imbue_list(self.get_tile_comps())

    """ Special """

    def __eq__(self, other):
        if not isinstance(other, Field):
            return False
        return other.world_coord == self.world_coord

    def __ne__(self, other):
        return not self.__eq__(other)
