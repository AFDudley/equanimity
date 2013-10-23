"""
stronghold.py

Created by AFD on 2013-08-05.
Copyright (c) 2013 A. Frederick Dudley. All rights reserved.
"""
from collections import OrderedDict
from persistent import Persistent
from persistent.mapping import PersistentMapping

from server import db

from stone import Stone
from units import Scient
from unit_container import Squad
from weapons import weapons
from unit_container import Container
from const import ORTH, OPP, WEP_LIST, ELEMENTS
from factory import Stable, Armory, Home, Farm
from silo import Silo
from copy import deepcopy
from clock import now


class MappedContainer(Container):
    def __init__(self):
        super(MappedContainer, self).__init__(data=None, free_spaces=32)
        #maybe map should actually return the key and method
        #should be added instead of using .map
        self.map = PersistentMapping()
        self.name = 'stronghold'

    def __getitem__(self, key):
        return self.map[key]

    def __setitem__(self, key, unit):
        if key != unit.uid:
            raise KeyError('Key must equal unit uid')
        self.append(unit)

    def __delitem__(self, key):
        unit = self.map[key]
        super(MappedContainer, self).__delitem__(self.units.index(unit))
        del self.map[key]

    def __contains__(self, key):
        return (key in self.map)

    def append(self, unit):
        if unit.uid in self.map:
            pos = self.units.index(unit)
            super(MappedContainer, self).__setitem__(pos, unit)
        else:
            super(MappedContainer, self).append(unit)
        self.map[unit.uid] = unit

    def pop(self, unit_id):
        unit = self.map[unit_id]
        del self[unit_id]
        return unit


class SparseList(Persistent):

    """ Array-like, but removing an element does not reorder the remaining
    elements """

    def __init__(self):
        self.index = 0
        self.items = OrderedDict()

    def append(self, item):
        self.items[self.index] = item
        self.index += 1
        return self.index - 1

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

    def get(self, key):
        return self.items.get(key)

    def pop(self, key):
        return self.items.pop(key)


class Stronghold(Persistent):

    def __init__(self, field):
        self._defenders = None
        self.field = field
        self.silo = Silo()
        self.weapons = SparseList()
        self.free_units = MappedContainer()
        self.units = dict()
        self.squads = SparseList()
        self.defenders = self.form_squad(name='Defenders')
        self._setup_default_defenders(field.element)
        self.stable = None
        self.armory = None
        self.home = None
        self.farm = None
        self.create_factory(field.element)

    @property
    def defenders(self):
        if self._defenders is not None:
            return self.squads[self._defenders]

    @defenders.setter
    def defenders(self, val):
        if hasattr(val, 'stronghold_pos'):
            if val.stronghold != self:
                raise ValueError('Squad must be in stronghold before setting '
                                 'it as a defender')
            val = val.stronghold_pos
        elif val is not None and val not in self.squads.items:
            raise ValueError('Unknown squad at position {}'.format(val))
        self._defenders = val

    @property
    def location(self):
        return self.field.world_coord

    @property
    def clock(self):
        return self.field.clock

    @property
    def owner(self):
        return self.field.owner

    @classmethod
    def get(self, field_location):
        field = db['fields'].get(tuple(field_location))
        if field is not None:
            return field.stronghold

    def api_view(self):
        defenders = self.defenders
        if defenders is None:
            defenders = {}
        else:
            defenders = defenders.api_view()
        return dict(
            field=self.field.world_coord, silo=self.silo.api_view(),
            weapons=[w.api_view() for w in self.weapons],
            free_units=[u.api_view() for u in self.free_units],
            squads=[s.api_view() for s in self.squads],
            defenders=defenders)

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
        return factory

    def form_weapon(self, element, comp, weap_type):
        """Takes a stone from stronghold and turns it into a Weapon."""
        if weap_type not in weapons:
            raise ValueError('Invalid weapon type "{0}"'.format(weap_type))
        if element not in ELEMENTS:
            raise ValueError('Invalid element "{0}"'.format(element))
        weapon = weapons[weap_type](element, self.silo.get(comp))
        pos = self.weapons.append(weapon)
        weapon.add_to_stronghold(self, pos)
        return weapon

    def imbue_weapon(self, comp, weapon_num):
        """Imbue a weapon with stone of comp from silo."""
        stone = self.silo.get(comp)
        weapon = self.weapons[weapon_num]
        weapon.imbue(stone)
        return weapon

    def split_weapon(self, comp, weapon_num):
        """Splits comp from weapon, places it in silo."""
        stone = self.weapons[weapon_num].split(comp)
        self.silo.imbue(stone)
        return self.weapons[weapon_num]

    def form_scient(self, element, comp, name=None):
        """Takes a stone from stronghold and turns it into a Scient."""
        comp = self.silo.get(comp)
        scient = Scient(element, comp, name=name)
        scient.owner = self.owner
        self.free_units.append(scient)
        self.units[scient.uid] = scient
        self.feed_unit(scient.uid)
        return scient

    def name_unit(self, unit_id, name):
        unit = self.units[unit_id]
        unit.name = name
        return unit

    def imbue_unit(self, comp, unit_id):
        """Imbue a unit with stone of comp from silo."""
        stone = self.silo.get(comp)
        unit = self.units[unit_id]
        unit.imbue(stone)
        if unit.container.name != 'stronghold':
            unit.container._update_value()
        return unit

    def unequip_scient(self, unit_id):
        """Moves a weapon from a scient to the stronghold."""
        unit = self.units[unit_id]
        weapon = unit.unequip()
        pos = self.weapons.append(weapon)
        weapon.add_to_stronghold(self, pos)
        return weapon

    def equip_scient(self, unit_id, weapon_num):
        """Moves a weapon from the weapon list to a scient."""
        scient = self.units[unit_id]
        if scient.weapon is not None:
            self.unequip_scient(unit_id)
        weapon = self.weapons.pop(weapon_num)
        weapon.remove_from_stronghold()
        scient.equip(weapon)
        return scient

    def form_squad(self, unit_ids=tuple(), name=None):
        """Forms a squad and places it in the stronghold."""
        sq = Squad(owner=self.owner, name=name)
        for unit_id in unit_ids:
            unit = self.free_units.pop(unit_id)
            try:
                sq.append(unit)
            except Exception:
                # Put it back in case there was error
                self.free_units.append(unit)
        pos = self.squads.append(sq)
        sq.add_to_stronghold(self, pos)
        return sq

    def name_squad(self, squad_num, name):
        squad = self.squads[squad_num]
        squad.name = name
        return squad

    def remove_squad(self, squad_num):
        """Removes units from from self.units, effectively moving the squad out
         of the stronghold."""
        squad = self.squads.pop(squad_num)
        squad.remove_from_stronghold()
        return squad

    def apply_locs_to_squad(self, squad, list_of_locs):
        """takes a list of locations and appliees them to the units in a
        squad"""
        #TODO loc sanity check. on_grid is a start, but not completely correct.
        if len(squad) != len(list_of_locs):
            raise Exception("The squad and the list of locations must be the "
                            "same length.")
        for n in xrange(len(squad)):
            squad[n].location = list_of_locs[n]
            squad[n]._p_changed = 1

    def _setup_default_defenders(self, element):
        """ TODO -- remove this """
        s = Stone()
        s[element] = 4
        s[OPP[element]] = 0
        for o in ORTH[element]:
            s[o] = 2
        for n in xrange(8):
            self.silo.imbue(deepcopy(s))
        wcomp = Stone().comp
        for i, wep in enumerate(WEP_LIST):
            unit = self.form_scient(element, s.comp)
            self.form_weapon(element, wcomp, wep)
            self.name_unit(unit.uid, "Ms. " + wep)
            self.equip_scient(unit.uid, i)
            self.add_unit_to_defenders(unit.uid)

    def move_squad_to_defenders(self, squad_num):
        """Moves a squad from self.squads to self.defenders"""
        self.defenders = squad_num

    def remove_defenders(self):
        self.defenders = None

    def _add_unit_to(self, container, unit_id):
        """Add unit to container."""
        #wrapper to keep containers private.
        container.append(self.free_units[unit_id])

    def add_unit_to_defenders(self, unit_id):
        return self._add_unit_to(self.defenders, unit_id)

    def add_unit_to_factory(self, kind, unit_id):
        if kind == 'Stable':
            return self._add_unit_to(self.stable, unit_id)
        elif kind == 'Armory':
            return self._add_unit_to(self.armory, unit_id)
        elif kind == 'Home':
            return self._add_unit_to(self.home, unit_id)
        elif kind == 'Farm':
            return self._add_unit_to(self.farm, unit_id)

    def add_unit_to_squad(self, squad_num, unit_id):
        return self._add_unit_to(self, self.squads[squad_num], unit_id)

    def _remove_unit_from(self, container, unit_id):
        """remove unit from a container, either a stronghold or a squad. """
        if container == self:
            del self.free_units[unit_id]
        else:
            stronghold = getattr(container, 'stronghold', None)
            if stronghold is None or stronghold != self:
                raise ValueError('Unit container has no relation to this '
                                 'stronghold')
            container.remove(self.units[unit_id])
        del self.units[unit_id]

    def remove_unit_from_defenders(self, unit_id):
        return self._remove_unit_from(self.defenders, unit_id)

    def remove_unit_from_factory(self, kind, unit_id):
        if kind == 'Stable':
            return self._remove_unit_from(self.stable, unit_id)
        elif kind == 'Armory':
            return self._remove_unit_from(self.armory, unit_id)
        elif kind == 'Home':
            return self._remove_unit_from(self.home, unit_id)
        elif kind == 'Farm':
            return self._remove_unit_from(self.farm, unit_id)

    def remove_unit_from_squad(self, squad_num, unit_id):
        return self._remove_unit_from(self.squads[squad_num], unit_id)

    def bury_unit(self, unit_id):
        """Bury units that die outside of battle."""
        unit = self.units[unit_id]
        self.unequip_scient(unit)
        self._remove_unit_from(unit.container, unit.uid)
        remains = Stone({k: v / 2 for k, v in unit.iteritems()})
        self.silo.imbue(remains)
        del self.units[unit_id]

    def feed_unit(self, unit_id):  # maybe it should take a clock.
        """feeds a unit from the silo, most they can be fed is every 60 days"""
        # A scient eats their composition's worth of stones in 2 months.
        # (60 days)
        # every two months from when the unit was born, discount the inventory
        # the unit's value.
        # Two weeks without food a unit dies.

        def feed(unit, lnow):
            self.silo.get(unit.comp)
            unit.fed_on = now()

        unit = self.units[unit_id]
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
