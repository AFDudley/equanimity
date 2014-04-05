"""
stronghold.py

Created by AFD on 2013-08-05.
Copyright (c) 2013 A. Frederick Dudley. All rights reserved.
"""
from collections import OrderedDict
from persistent import Persistent

from worldtools import get_world
from stone import Stone
from units import Scient
from unit_container import Squad, rand_squad, MappedContainer
from weapons import weapons
from const import ORTH, OPP, WEP_LIST, ELEMENTS
from factory import Stable, Armory, Home, Farm
from silo import Silo
from clock import now


class Stronghold(Persistent):

    @classmethod
    def get(self, world, field_location):
        w = get_world(world)
        if w is not None:
            field = w.fields.get(tuple(field_location))
            if field is not None:
                return field.stronghold

    def __init__(self, field):
        self._defenders = None
        self.field = field
        self.silo = Silo()
        self.weapons = SparseStrongholdList(self)
        self.free = MappedContainer(max_size=0)
        self.squads = SparseStrongholdList(self)
        self.defenders = None
        self.stable = None
        self.armory = None
        self.home = None
        self.farm = None
        # self.create_factory(field.element)

    @property
    def location(self):
        return self.field.world_coord

    @property
    def owner(self):
        return self.field.owner

    @property
    def units(self):
        """ Returns the sum of free and squad units """
        units = {}
        units.update(self.free.map)
        for sq in self.squads:
            for u in sq:
                units[u.uid] = u
        return units

    @property
    def occupancy(self):
        """ Returns spaces used by occupying units """
        sizes = [sq.size for sq in self.squads]
        return sum(sizes) + self.free.size

    @property
    def max_occupancy(self):
        base = self.field.grid.value + 4
        spaces = base // 64
        if base % 64:
            spaces += 1
        return spaces * 8

    @property
    def garrisoned(self):
        """ Returns True if there are units somewhere inside the stronghold
        """
        return self.occupancy > 0

    def api_view(self):
        defenders = {}
        if self.defenders is not None:
            defenders = self.defenders.api_view()
        return dict(
            field=self.location,
            silo=self.silo.api_view(),
            weapons=[w.api_view() for w in self.weapons],
            free=[u.api_view() for u in self.free],
            squads=[s.api_view() for s in self.squads],
            defenders=defenders,
        )

    def populate(self, kind=None, size=8):
        """ Adds an initial squad of scients to the stronghold """
        if self.garrisoned:
            raise ValueError("Stronghold is already occupied")
        
        squad = rand_squad(owner=self.owner, element=self.field.element,
                           max_value=self.field.grid.value, size=size,
                           kind=kind, equip=True)
        self._add_squad(squad)

    def add_free_unit(self, unit):
        """ Adds a unit to the free units """
        if self.occupancy + unit.size > self.max_occupancy:
            raise ValueError("Not enough room in stronghold to add unit")
        if unit.uid in self.free:
            raise ValueError("Unit is already in free units")
        if unit.container is not None:
            unit.container.remove(unit)
        unit.owner = self.owner
        self.free.append(unit)

    """ Defender management """

    @property
    def defenders(self):
        sq = self.squads.get(self._defenders)
        if sq is None:
            sq = self._get_automatic_defenders()
            self.defenders = sq
        return sq

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

    def move_squad_to_defenders(self, squad_num):
        """Moves a squad from self.squads to self.defenders"""
        self.defenders = squad_num

    def remove_defenders(self):
        self.defenders = None

    def add_unit_to_defenders(self, unit_id):
        return self._add_unit_to(self.defenders, unit_id)

    def remove_unit_from_defenders(self, unit_id):
        return self._remove_unit_from(self.defenders, unit_id)

    """ Squad management """

    def move_squad_out(self, squad_num, direction):
        """ Moves a squad to an adjacent's field's queue. Returns True if
        there is an adjacent field. """
        f = self.field.get_adjacent(direction)
        if f is not None:
            f.queue.add(f, self.squads[squad_num])
            return True
        return False

    def move_squad_in(self, squad):
        """ Move foreign squad into here """
        if squad.size + self.occupancy > self.max_occupancy:
            raise ValueError("Not enough room in stronghold for squad")
        if squad.stronghold is not None:
            squad.stronghold.remove_squad(squad.stronghold_pos)
        self._add_squad(squad)

    def form_squad(self, unit_ids=tuple(), name=None):
        """Forms a squad and places it in the stronghold."""
        sq = Squad(owner=self.owner, name=name)
        for unit_id in unit_ids:
            unit = self.free.pop(unit_id)
            try:
                sq.append(unit)
            except ValueError:
                # Put it back in case there was error
                self.free.append(unit)
        self.squads.append(sq)
        return sq

    def name_squad(self, squad_num, name):
        squad = self.squads[squad_num]
        squad.name = name
        return squad

    def remove_squad(self, squad_num):
        """Removes and returns the squad from this stronghold. The units
        remain in the squad."""
        if squad_num == self._defenders:
            self._defenders = None
        squad = self.squads.pop(squad_num)
        return squad

    def disband_squad(self, squad_num):
        """ Removes the squad from this stronghold, placing its units in the
        free units pool."""
        squad = self.squads[squad_num]
        while squad:
            self._remove_unit_from(squad, squad[0].uid)
        del self.squads[squad_num]

    """ Unit management """

    def form_scient(self, element, comp, name=None):
        """Takes a stone from stronghold and turns it into a Scient."""
        if self.occupancy + Scient.size > self.max_occupancy:
            raise ValueError("Not enough room in stronghold to form Scient")
        comp = self.silo.get(comp)
        scient = Scient(element, comp, name=name)
        self.add_free_unit(scient)
        self.feed_unit(scient.uid)
        return scient

    def unequip_scient(self, unit_id):
        """Moves a weapon from a scient to the stronghold."""
        unit = self.units[unit_id]
        weapon = unit.unequip()
        self.weapons.append(weapon)
        return weapon

    def equip_scient(self, unit_id, weapon_num):
        """Moves a weapon from the weapon list to a scient."""
        scient = self.units[unit_id]
        if scient.weapon is not None:
            self.unequip_scient(unit_id)
        weapon = self.weapons.pop(weapon_num)
        scient.equip(weapon)
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
        return unit

    def add_unit_to_squad(self, squad_num, unit_id):
        return self._add_unit_to(self, self.squads[squad_num], unit_id)

    def remove_unit_from_squad(self, squad_num, unit_id):
        return self._remove_unit_from(self.squads[squad_num], unit_id)

    def bury_unit(self, unit_id):
        """Bury units that die outside of battle."""
        unit = self.units[unit_id]
        self.unequip_scient(unit)
        self._remove_unit_from(unit.container, unit.uid)
        remains = Stone({k: v / 2 for k, v in unit.iteritems()})
        self.silo.imbue(remains)
        self._remove_unit_from(unit.container, unit.uid)

    def feed_unit(self, unit_id):  # maybe it should take a clock.
        """Feeds a unit from the silo, most they can be fed is every 60 days"""
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
            if dsecs > (self.field.clock.duration['day'] * 60):
                if dsecs < (self.field.clock.duration['day'] * 72):
                    feed(unit, lnow)
                else:
                    self.bury_unit(unit_id)
            else:
                pass  # unit already fed.

    def feed_units(self):
        """Attempts to feed units. check happens every game day."""
        # 1. feed scients first.
        # 2. feed nescients.
        # should not happen when field is embattled.
        n = now()
        for unit in self.units:
            d = n - unit.fed_on
            dsecs = d.total_seconds()
            if dsecs > (self.field.clock.duration['day'] * 60):
                self.feed_unit(unit.uid)

    """ Weapon management """

    def form_weapon(self, element, comp, weap_type):
        """Takes a stone from stronghold and turns it into a Weapon."""
        if weap_type not in weapons:
            raise ValueError('Invalid weapon type "{0}"'.format(weap_type))
        if element not in ELEMENTS:
            raise ValueError('Invalid element "{0}"'.format(element))
        weapon = weapons[weap_type](element, self.silo.get(comp))
        self.weapons.append(weapon)
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

    """ Factory management """

    def create_factory(self, kind):
        """Adds a factory to a stronghold, raises exception if factory already
        exists."""
        # factories should cost something.
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

    def add_unit_to_factory(self, kind, unit_id):
        if kind == 'Stable':
            return self._add_unit_to(self.stable, unit_id)
        elif kind == 'Armory':
            return self._add_unit_to(self.armory, unit_id)
        elif kind == 'Home':
            return self._add_unit_to(self.home, unit_id)
        elif kind == 'Farm':
            return self._add_unit_to(self.farm, unit_id)

    def remove_unit_from_factory(self, kind, unit_id):
        if kind == 'Stable':
            return self._remove_unit_from(self.stable, unit_id)
        elif kind == 'Armory':
            return self._remove_unit_from(self.armory, unit_id)
        elif kind == 'Home':
            return self._remove_unit_from(self.home, unit_id)
        elif kind == 'Farm':
            return self._remove_unit_from(self.farm, unit_id)

    """ Special """

    def __eq__(self, other):
        if not isinstance(other, self.__class__):
            return False
        else:
            return self.field == other.field

    def __ne__(self, other):
        return not self.__eq__(other)

    """ Internal """

    def _add_squad(self, squad):
        """ Adds an already existing squad to this stronghold """
        if squad.stronghold == self:
            raise ValueError('Can\'t move squad to same stronghold')
        if squad.stronghold is not None:
            msg = 'Squad {0} is in another stronghold'
            raise ValueError(msg.format(squad))
        if squad.owner != self.owner:
            msg = 'Squad {0} does not have same owner as stronghold'
            raise ValueError(msg.format(squad))
        if squad.size + self.occupancy > self.max_occupancy:
            raise ValueError('Stronghold does not have enough room for squad')
        self.squads.append(squad)

    def _add_unit_to(self, container, unit_id):
        """Add unit to a container from free"""
        if container.stronghold != self:
            raise ValueError('Container is not related to stronghold')
        unit = self.free.pop(unit_id)
        container.append(unit)

    def _remove_unit_from(self, container, unit_id):
        """remove unit from a container, either a stronghold or a squad. """
        if container == self:
            # If the unit is in free units, remove it from the stronghold
            del self.free[unit_id]
        else:
            # Otherwise, move the unit into the free units
            if container.stronghold != self:
                raise ValueError("Container is not related to stronghold")
            unit = container.get(unit_id)
            if unit is None:
                raise ValueError("Unit is not related to this container")
            container.remove(unit)
            self.free.append(unit)

    def _get_automatic_defenders(self):
        """ Returns the highest valued squad, if one exists. Otherwise
        it forms a squad from the highest valued free units available.
        If no free units are available, it is an error because this should
        have reverted to a world owned stronghold which is never empty. """
        squad = self._get_most_valuable_squad()
        if squad is None:
            return self._create_automatic_free_unit_squad()
        else:
            return squad

    def _get_most_valuable_squad(self):
        """ Return the highest value squad, if there is one """
        highest = None
        highest_val = -1
        for s in self.squads:
            if s.value > highest_val:
                highest = s
                highest_val = s.value
        return highest

    def _create_automatic_free_unit_squad(self):
        """ Create a squad from the highest valued free units """
        if not self.free:
            return
        units = self.free.sorted_by_value(descending=True)
        units = [unit.uid for unit in units]
        return self.form_squad(unit_ids=units, name='Defenders')

    def _setup_default_defenders(self, element=None, name='Defenders'):
        """ TODO -- remove this -- its either a testing method,
        which should be in the tests, or a method for initializing fields
        with some units. """
        if self._defenders is not None:
            raise ValueError('Defenders already set up')
        if element is None:
            element = self.field.element
        s = Stone()
        s[element] = 4
        s[OPP[element]] = 0
        for o in ORTH[element]:
            s[o] = 2
        for n in xrange(8):
            self.silo.imbue(s.copy())
        wcomp = Stone().comp
        units = []
        for wep in WEP_LIST:
            unit = self.form_scient(element, s.comp)
            units.append(unit)
            w = self.form_weapon(element, wcomp, wep)
            self.name_unit(unit.uid, "Ms. " + wep)
            self.equip_scient(unit.uid, w.stronghold_pos)
        s = self.form_squad(unit_ids=[u.uid for u in units], name=name)
        self.defenders = s
        return s


class SparseList(Persistent):

    """ Array-like, but removing an element does not reorder the remaining
    elements """

    def __init__(self):
        self.index = 0
        self.items = OrderedDict()

    def append(self, item):
        while self.index in self.items:
            self.index += 1
        self.items[self.index] = item
        self._p_changed = 1
        return self.index

    def __len__(self):
        return len(self.items)

    def __getitem__(self, pos):
        return self.items[pos]

    def __setitem__(self, pos, item):
        self.items[pos] = item
        self._p_changed = 1

    def __delitem__(self, pos):
        del self.items[pos]
        self._p_changed = 1

    def __iter__(self):
        return self.items.itervalues()

    def __repr__(self):
        return repr(list(self))

    def get(self, key, default=None):
        return self.items.get(key, default)

    def pop(self, key):
        self._p_changed = 1
        return self.items.pop(key)


class SparseStrongholdList(SparseList):

    def __init__(self, stronghold):
        super(SparseStrongholdList, self).__init__()
        self.stronghold = stronghold

    def append(self, item):
        pos = super(SparseStrongholdList, self).append(item)
        item.add_to_stronghold(self.stronghold, pos)
        return pos

    def __setitem__(self, pos, item):
        if pos in self.items:
            raise ValueError('Can\'t overwrite item at {0}'.format(pos))
        super(SparseStrongholdList, self).__setitem__(pos, item)
        item.add_to_stronghold(self.stronghold, pos)

    def pop(self, key):
        item = super(SparseStrongholdList, self).pop(key)
        item.remove_from_stronghold()
        return item

    def __delitem__(self, pos):
        item = self.items[pos]
        super(SparseStrongholdList, self).__delitem__(pos)
        item.remove_from_stronghold()
