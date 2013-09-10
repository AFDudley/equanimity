"""
field.py

Created by AFD on 2013-08-05.
Copyright (c) 2013 A. Frederick Dudley. All rights reserved.
"""
import transaction
import persistent
from math import ceil

from stone import Stone
from helpers import get_element
from grid import Grid
from player import Player, WorldPlayer
from battle import Game
from stronghold import Stronghold
from clock import Clock


class Field(persistent.Persistent):
    """Player owned field logic."""
    def __init__(self, world_coord, owner=None, ply_time=240):
        self.locked = False
        self.world_coord = world_coord
        if owner is None:
            owner = WorldPlayer.get()
        self.owner = owner
        self.grid = Grid()
        self.element = 'Ice'  # For testing
        #self.element = get_element(self.grid.comp)
        self.clock = Clock()
        self.stronghold = Stronghold(self.owner, self.element, self.clock)
        self.plantings = persistent.mapping.PersistentMapping()
        self.attackerqueue = persistent.list.PersistentList()
        self.game = None
        self.state = 'produce'  # Default state
        """
        ply_time: user definable time before a pass is automatically sent
        for a battle action.
        range between 4 and 360 minutes, default is 4 (in seconds)
        """
        self.ply_time = ply_time
        self.battle_actions = ['attack', 'move', 'pass', 'timed_out']
        self.stronghold_actions = [
            'add_planting', 'name_unit', 'imbue_unit', 'unequip_scient',
            'equip_scient', 'move_unit', 'imbue_weapon', 'split_weapon',
            'form_squad', 'name_suqad', 'remove_squad', 'set_squad_locations',
            'set_defender_locations', 'move_squad_to_defenders',
            'unset_defenders',
        ]
        self.world_actions = ['move_squad']
        self.actions = (self.battle_actions + self.stronghold_actions +
                        self.world_actions)

    def setup_battle(self):
        # TODO (steve) -- this is a helper method for testing
        # and needs to be replaced
        # load the battlefield with players (and squads)
        atkr_name, atksquad = self.attackerqueue[0]  # TODO change to pop
        defsquad = self.get_defenders()
        self.owners.squads = [defsquad]
        atkr = Player.get(1)
        atkr.squads = [atksquad]
        # TODO write a new game object.
        self.game = Game(grid=self.grid, defender=self.owner, attacker=atkr)
        # place units on battlefield
        # TODO (steve) -- the defender accesses the stronghold to predetermine
        # how its units will be placed at the start of a battle?
        # If so, that needs to be stored on a separate field besides
        # unit.location so it can be reset properly.
        # Also in that case, how is the attacker's placement chosen?
        self.game.put_squads_on_field()
        return transaction.commit()

    def set_owner(self, owner):
        self.owner = owner
        return transaction.commit()

    def change_state(self):
        # called everyday by world?
        # should be a proper state machine, too focused to find one.
        if self.battleque:
            if self.state == 'produce':
                self.state = 'battle'
                self.setup_battle()
            else:
                pass

        elif self.element == self.clock.get_time('season'):
            self.state = 'harvest'
        else:
            self.state = 'produce'
        return transaction.commit()

    def get_defenders(self):
        """gets the defenders of a Field."""
        try:
            return self.stronghold.defenders
        except:
            raise Exception("Stronghold has no defenders.")

    def set_stronghold_capacity(self):
        """Uses grid.value to determine stronghold capacity."""
        # squad points. scient = 1 nescient = 2
        # capacity increases at:
        # [61, 125, 189, 253, 317, 381, 445, 509, 573, 637, 701, 765, 829,
        #  893, 957,]
        spaces = ceil((self.grid.value() + 4) / 64.0)
        self.stronghold.units.free_spaces = int(spaces) * 8
        self.stronghold.units._p_changed = 1
        return transaction.commit()

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
        return transaction.commit()

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
                return transaction.commit()

    def harvest(self):
        """returns set of stones generated at harvest"""
        #this needs to be more clever and relate to the units in
        #the stronghold somehow.
        #happens once a year.
        return self.stronghold.silo.imbue_list(self.get_tile_comps())


"""
--- In battle
pass
attack
move
timed_out
--- In stronghold
add_planting (imbue_tile) - tile_coord, comp

name_unit  - unit_id, name
imbue_unit - unit_id, comp
unequip_scient - unit_id
equip_scient - unit_id, weapon_num
move_unit (add_unit_to) - unit_id, container

imbue_weapon
split_weapon

form_squad
name_squad

remove_squad
set_squad_locations

set_defender_locations
move_squad_to_defenders
unset_defenders

--- In world
move_squad
TODO: send_stone, stone, field
"""
