"""
field.py

Created by AFD on 2013-08-05.
Copyright (c) 2013 A. Frederick Dudley. All rights reserved.
"""
import random
from persistent import Persistent
from collections import OrderedDict

from worldtools import get_world
from stone import Stone, get_element
from grid import Grid, Hex
from player import WorldPlayer
from battle import Battle
from stronghold import Stronghold
from clock import FieldClock
from unit_container import Squad
from const import FIELD_BATTLE


class FieldQueue(Persistent):

    """ Manages requests to move into a field """

    def __init__(self):
        self.flush()

    def flush(self):
        self.queue = OrderedDict()

    def add(self, field, squad):
        if squad.stronghold is None:
            msg = 'Squad must be in a stronghold to move to a field'
            raise ValueError(msg)
        sq_pos = squad.stronghold.location
        if not field.grid.is_adjacent(field.world_coord, sq_pos):
            raise ValueError('Fields must be adjacent')
        slot = sq_pos - field.world_coord
        if slot in self.queue:
            raise ValueError('Queue slot is taken')
        self.queue[slot] = squad
        squad.queue_at(field)
        self._p_changed = 1

    def pop(self):
        """ Removes and returns the next item in the queue """
        if self.queue:
            s = self.queue.popitem(last=False)[1]
            s.unqueue()
            self._p_changed = 1
            return s

    def as_array(self):
        return [dict(squad=sq.api_view(), slot=k)
                for k, sq in self.queue.iteritems()]


class Field(Persistent):

    """Player owned field logic."""

    @classmethod
    def get(self, world, loc):
        w = get_world(world)
        if w is not None:
            return w.fields.get(tuple(loc))

    def __init__(self, world, coord, element, owner=None, grid=None):
        self.world = world
        self.world_coord = Hex._make(coord)
        if grid is None:
            grid = Grid()
        self.grid = grid
        self.element = element
        self.clock = FieldClock()
        self.stronghold = Stronghold(self)
        self.queue = FieldQueue()
        self.plantings = {}
        self.battle = None
        self._owner = None
        if owner is None:
            owner = WorldPlayer.get()
        self.owner = owner

    def api_view(self, requester=None):
        if requester is not None:
            visible = requester.get_visible_fields(self.world.uid)
            if self.world_coord not in visible:
                return {}
        # TODO -- add factory etc stuff
        return dict(owner=self.owner.uid,
                    element=self.element,
                    coordinate=self.world_coord,
                    state=self.state,
                    clock=self.clock.api_view(),
                    queue=self.queue.as_array(),
                    battle=getattr(self.battle, 'uid', None))

    @property
    def in_battle(self):
        return (self.battle is not None and not self.battle.state['game_over'])

    @property
    def state(self):
        if self.in_battle:
            return FIELD_BATTLE
        else:
            return self.clock.state(self)

    @property
    def owner(self):
        return self._owner

    @owner.setter
    def owner(self, owner):
        self._owner = owner
        for s in self.stronghold.squads:
            s.owner = owner
        for u in self.stronghold.free:
            u.owner = owner

    def get_adjacent(self, direction):
        """ Returns the field adjacent to this one in a given direction.
        Returns None if at the border. """
        t = self.world.grid.get_adjacent(self.world_coord, direction=direction)
        if t:
            return self.world.fields.get(tuple(tuple(t)[0]))

    def process_battle_and_movement(self):
        """ Starts a battle if an attacker is available, otherwise moves
        a friendly squad into the stronghold if available """
        # First, check if there was a previous battle and if it is over
        if self.battle is not None and self.battle.state['game_over']:
            # If the winner is not the owner, that means the stronghold was
            # still garrisoned, and we must start a new battle
            if self.battle.winner != self.owner:
                self.start_battle(self.battle.battlefield.atksquad)
        else:
            next_squad = self.queue.pop()
            if next_squad is not None:
                if next_squad.owner == self.owner:
                    self.stronghold.move_squad_in(next_squad)
                else:
                    self.start_battle(next_squad)

    def start_battle(self, attacking_squad):
        self.battle = Battle(self, attacking_squad)
        self.battle.persist()
        self.battle.start()

    def check_ungarrisoned(self):
        """ Reverts ownership to the WorldPlayer if unoccupied """
        wp = WorldPlayer.get()
        if self.owner != wp and not self.stronghold.garrisoned:
            self.owner = wp

    def get_taken_over(self, atkr):
        """ Transfers a winning attacking squad to the field. Returns False
        if the stronghold is still controlled. """
        if self.stronghold.garrisoned:
            return False
        self.owner = atkr.owner
        self.stronghold.move_squad_in(self.battlefield.atksquad)
        return True

    def place_scient(self, unit, location):
        if getattr(unit, 'type', '') != 'scient':
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
        # this uses get_tile_comps so the / 8 is only maintained in one place.
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
                self.set_silo_limit()

    def harvest(self):
        """returns set of stones generated at harvest"""
        # this needs to be more clever and relate to the units in
        # the stronghold somehow.
        # happens once a year.
        return self.stronghold.silo.imbue_list(self.get_tile_comps())

    """ Special """

    def __eq__(self, other):
        if not isinstance(other, Field):
            return False
        return (other.world == self.world and
                other.world_coord == self.world_coord)

    def __ne__(self, other):
        return not self.__eq__(other)
