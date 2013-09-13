"""
stronghold.py

Created by AFD on 2013-08-05.
Copyright (c) 2013 A. Frederick Dudley. All rights reserved.
"""
import transaction
import itertools
from collections import OrderedDict
from persistent import Persistent
from persistent.mapping import PersistentMapping
from persistent.list import PersistentList

from server import db

from stone import Stone
from units import Scient
from unit_container import Container, Squad
from weapons import weapons
from const import ORTH, OPP, WEP_LIST, ELEMENTS
from grid import Hex
from helpers import rand_string
from factory import Stable, Armory, Home, Farm
from silo import Silo
from copy import deepcopy
from clock import now


class MappedContainer(Container):
    def __init__(self):
        super(MappedContainer, self).__init__(data=None, free_spaces=8)
        #maybe map should actually return the key and method
        #should be added instead of using .map
        self.map = PersistentMapping()
        self.name = 'stronghold'

    def __setitem__(self, key, val):
        super(MappedContainer, self).__setitem__(key, val)
        self.map.update({key.uid: key})

    def __delitem__(self, key):
        del self.map[self.units[key].uid]
        if self.units[key].container.name == 'stronghold':
            self.units[key].container = None
        temp = self[key].value()
        self.free_spaces += self[key].size
        del self.units[key]
        self.val -= temp

    def append(self, item):
        super(MappedContainer, self).append(item)
        self.map.update({item.uid: item})

    def remove_by_id(self, unit_id):
        # TODO FIX
        k = None
        for u_key in reversed(xrange(len(self))):
            if self[u_key].uid == unit_id:
                k = u_key
        del self[k]


class SparseList(Persistent):

    """ Array-like, but removing an element does not reorder the remaining
    elements """

    def __init__(self):
        self.index = 0
        self.items = OrderedDict()

    def append(self, item):
        self.items[self.index + 1] = item
        self.index += 1

    def __len__(self):
        return len(self.items)

    def __getitem__(self, pos):
        return self.items[pos]

    def __setitem__(self, pos, item):
        self.items[pos] = item

    def __delitem__(self, pos):
        del self.items[pos]

    def __iter__(self):
        return self.items.itervalues()

    def __repr__(self):
        return repr(list(self))


class Stronghold(Persistent):

    def __init__(self, field):
        self.field = field
        self.silo = Silo()
        self.weapons = PersistentList()
        self.free_units = MappedContainer()
        self.squads = SparseList()
        self.defenders = Squad(owner=field.owner, name='Defenders')
        self.make_defenders(field.element)
        self.defender_locs = PersistentList()
        self.stable = None
        self.armory = None
        self.home = None
        self.farm = None
        self.create_factory(field.element)
        transaction.commit()

    @property
    def clock(self):
        return self.field.clock

    @property
    def owner(self):
        return self.field.owner

    @property
    def units(self):
        print list(self.free_units)
        print self.squads
        return list(itertools.chain(self.free_units,
                                    *list(self.squads)))

    @classmethod
    def get(self, field_location):
        field_location = Hex._make(field_location)
        field = db['fields'].get(field_location)
        return field.stronghold

    def create_factory(self, kind):
        """Adds a factory to a stronghold, raises exception if factory already
        exists."""
        #factories should cost something.
        if kind == 'Stable' or kind == 'Earth':
            if self.stable is None:
                factory = self.stable = Stable()
            else:
                raise ValueError("This stronghold already has a stable.")
        elif kind == 'Armory' or kind == 'Fire':
            if self.armory is None:
                factory = self.armory = Armory()
            else:
                raise ValueError("This stronghold already has an armory.")
        elif kind == 'Home' or kind == 'Ice':
            if self.home is None:
                factory = self.home = Home()
            else:
                raise ValueError("This stronghold already has a home.")
        elif kind == 'Farm' or kind == 'Wind':
            if self.farm is None:
                factory = self.farm = Farm()
            else:
                raise ValueError("This stronghold already has a farm.")
        else:
            raise ValueError("Unknown kind '{0}'".format(kind))
        transaction.commit()
        return factory

    def form_weapon(self, element, comp, weap_type):
        """Takes a stone from stronghold and turns it into a Weapon."""
        #for testing!!!!!
        #!!!!!!!!WEAP_TYPE NEEDS TO BE CHECKED BEFORE PASSED TO EVAL!!!!!!!!!!!
        #(or I could just fix Weapon, duh)
        if weap_type not in weapons:
            raise ValueError('Invalid weapon type "{0}"'.format(weap_type))
        if element not in ELEMENTS:
            raise ValueError('Invalid element "{0}"'.format(element))
        weapon = weapons[weap_type](element, self.silo.get(comp))
        self.weapons.append(weapon)
        self._p_changed = 1
        return transaction.commit()

    def imbue_weapon(self, comp, weapon_num):
        """Imbue a weapon with stone of comp from silo."""
        stone = self.silo.get(comp)
        weapon = self.weapons[weapon_num]
        weapon.imbue(stone)
        transaction.commit()
        return weapon

    def split_weapon(self, comp, weapon_num):
        """Splits comp from weapon, places it in silo."""
        stone = self.weapons[weapon_num].split(comp)
        self.silo.imbue(stone)
        return self.weapons[weapon_num]

    def form_scient(self, element, comp, name=None):
        """Takes a stone from stronghold and turns it into a Scient."""
        if name is None:
            name = rand_string()
        scient = Scient(element, self.silo.get(comp), name)
        self.free_units.append(scient)
        self.feed_unit(scient.uid)
        transaction.commit()
        return scient

    def name_unit(self, unit_id, name):
        unit = self.free_units.map[unit_id]
        unit.name = name
        transaction.commit()
        return unit

    def imbue_unit(self, comp, unit_id):
        """Imbue a unit with stone of comp from silo."""
        stone = self.silo.get(comp)
        unit = self.free_units.map[unit_id]
        unit.imbue(stone)
        if unit.container.name != 'stronghold':
            unit.container.update_value()
        transaction.commit()
        return unit

    def unequip_scient(self, unit_id):
        """Moves a weapon from a scient to the stronghold."""
        unit = self.free_units.map[unit_id]
        weapon = unit.unequip()
        self.weapons.append(weapon)
        transaction.commit()
        return weapon

    def equip_scient(self, unit_id, weapon_num):
        """Moves a weapon from the weapon list to a scient."""
        scient = self.free_units.map[unit_id]
        if scient.weapon:
            self.unequip_scient(unit_id)
        weapon = self.weapons[weapon_num]
        del self.weapons[weapon_num]
        scient.equip(weapon)
        transaction.commit()
        return scient

    def form_squad(self, unit_ids=tuple(), name=None):
        """Forms a squad and places it in the stronghold."""
        if name is None:
            name = rand_string()
        sq = Squad(owner=self.owner, name=name)
        for unit_id in unit_ids:
            unit = self.free_units.map[unit_id]
            sq.append(unit)
            del self.free_units.map[unit_id]
        self.squads.append(sq)
        transaction.commit()
        return sq

    def name_squad(self, squad_num, name):
        squad = self.squads[squad_num]
        squad.name = name
        transaction.commit()
        return squad

    def remove_squad(self, squad_num):
        """Removes units from from self.units, effectively moving the squad out
         of the stronghold."""
        squad = self.squads[squad_num]
        for unit in squad:
            self.units.remove_by_id(unit.uid)
        del self.squads[squad_num]
        transaction.commit()
        return self.squads

    def apply_locs_to_squad(self, squad, list_of_locs):
        """takes a list of locations and appliees them to the units in a
        squad"""
        #TODO loc sanity check. on_grid is a start, but not completely correct.
        if len(squad) == len(list_of_locs):
            for n in xrange(len(squad)):
                squad[n].location = list_of_locs[n]
                squad[n]._p_changed = 1
            return transaction.commit()
        else:
            raise Exception("The squad and the list of locations must be the "
                            "same length.")

    def apply_squad_locs(self, squad_num, list_of_locs):
        return self.apply_locs_to_squad(self.squads[squad_num], list_of_locs)

    def set_defender_locs(self, list_of_locs):
        self.defender_locs = list_of_locs
        self._p_changed = 1
        return transaction.commit()

    def apply_defender_locs(self):
        return self.apply_locs_to_squad(self.defenders, self.defender_locs)

    def unset_defenders(self):
        """Moves old defenders into stronghold"""
        #use wisely.
        self.squads.append(self.defenders)
        self.defenders = None
        self._p_changed = 1
        return transaction.commit()

    def set_defenders(self, squad_num):
        """If defenders is empty set squad as defenders."""
        # I don't remember how transactions work so I broke this function in
        # two, which might actually make it worse...

        # TODO: there should be a check to make sure the squad is not
        # stronger than the grid.
        # (Which is why self.defenders != self.squad[0])

        self.defenders = self.squads[squad_num]
        del self.squads[squad_num]
        self._p_changed = 1
        return transaction.commit()

    def make_defenders(self, element):
        """FIX"""
        s = Stone()
        s[element] = 4
        s[OPP[element]] = 0
        for o in ORTH[element]:
            s[o] = 2
        for n in xrange(8):
            self.silo.imbue(deepcopy(s))
        wcomp = Stone().comp
        for wep in WEP_LIST:
            self.form_scient(element, s.comp)
            # you wanna race?
            unit_id = self.units[-1].uid
            self.form_weapon(element, wcomp, wep)
            self.name_unit(unit_id, "Ms. " + wep)
            self.equip_scient(unit_id, -1)
            self.add_unit_to_defenders(unit_id)

    def move_squad_to_defenders(self, squad_num):
        """Moves a squad from self.squads to self.defenders"""
        try:
            self.unset_defenders()
            self.set_defenders(squad_num)
            return
        except:
            raise("There was an error moving squad to defenders.")

    def add_unit_to(self, container, unit_id):
        """Add unit to container."""
        #wrapper to keep containers private.
        container.append(self.free_units.map[unit_id])
        container._p_changed = 1
        return transaction.commit()

    def add_unit_to_defenders(self, unit_id):
        return self.add_unit_to(self.defenders, unit_id)

    def add_unit_to_factory(self, kind, unit_id):
        if kind == 'Stable':
            return self.add_unit_to(self.stable, unit_id)
        elif kind == 'Armory':
            return self.add_unit_to(self.armory, unit_id)
        elif kind == 'Home':
            return self.add_unit_to(self.home, unit_id)
        elif kind == 'Farm':
            return self.add_unit_to(self.farm, unit_id)

    def add_unit_to_squad(self, squad_num, unit_id):
        return self.add_unit_to(self, self.squads[squad_num], unit_id)

    def remove_unit_from(self, container, unit_id):
        """remove unit from container."""
        for n in xrange(len(container)):
            if container[n].uid == unit_id:
                container[n].container = None
                del container[n]
        container._p_changed = 1
        return transaction.commit()

    def remove_unit_from_defenders(self, unit_id):
        return self.remove_unit_from(self.defenders, unit_id)

    def remove_unit_from_factory(self, kind, unit_id):
        if kind == 'Stable':
            return self.remove_unit_from(self.stable, unit_id)
        elif kind == 'Armory':
            return self.remove_unit_from(self.armory, unit_id)
        elif kind == 'Home':
            return self.remove_unit_from(self.home, unit_id)
        elif kind == 'Farm':
            return self.remove_unit_from(self.farm, unit_id)

    def remove_unit_from_squad(self, squad_num, unit_id):
        return self.remove_unit_from(self.squads[squad_num], unit_id)

    def bury_unit(self, unit_id):
        """Bury units that die outside of battle."""
        unit = self.free_units.map[unit_id]
        self.unequip_scient(unit)
        self.remove_unit_from(unit.container, unit.uid)
        remains = Stone({k: v / 2 for k, v in unit.iteritems()})
        self.silo.imbue(remains)
        return

    def feed_unit(self, unit_id):  # maybe it should take a clock.
        """feeds a unit from the silo, most they can be fed is every 60 days"""
        # A scient eats their composition's worth of stones in 2 months.
        # (60 days)
        # every two months from when the unit was born, discount the inventory
        # the unit's value.
        # Two weeks without food a unit dies.

        def feed(unit, lnow):
            self.silo.get(unit.comp)
            self.silo._p_changed = 1
            unit.fed_on = now()
            unit._p_changed = 1
            return transaction.commit()

        unit = self.free_units.map[unit_id]
        lnow = now()
        if unit.fed_on is None:
            feed(unit, lnow)
        else:
            delta = lnow - unit.fed_on
            dsecs = delta.total_seconds()
            if dsecs > (self.clock.duration['day'] * 60):
                if dsecs < (self.clock.duration['day'] * 72):
                    feed(unit, lnow)
                else:
                    self.bury_unit(unit_id)
            else:
                pass  # unit already fed.

    def feed_units(self):
        """Attempts to feed units. check happens every game day."""
        # 1. feed scients first.
        # 2. feed nescients.
        #should not happen when field is embattled.
        n = now()
        for unit in self.units:
            d = n - unit.fed_on
            dsecs = d.total_seconds()
            if dsecs > (self.clock.duration['day'] * 60):
                self.feed_unit(unit.uid)

    def process_action(self, action):
        pass
