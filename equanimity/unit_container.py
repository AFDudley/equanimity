"""
unit_container.py

Created by AFD on 2013-03-06.
Copyright (c) 2013 A. Frederick Dudley. All rights reserved.
"""
from persistent import Persistent
from persistent.list import PersistentList
from stone import Stone
from const import ELEMENTS, WEP_LIST, OPP, ORTH
from units import Scient, rand_unit
from weapons import rand_weapon, weapons
from helpers import validate_length, rand_string, rand_element


SQUAD_NAME_LEN = dict(min=1, max=64)


class Container(Persistent):
    """contains units"""

    def __init__(self, data=None, free_spaces=8, owner=None):
        super(Container, self).__init__()
        if data is None:
            self.units = PersistentList()
        elif isinstance(data, Stone):
            self.units = PersistentList(initlist=[data])
        else:
            self.units = PersistentList(initlist=data)
        self.owner = owner
        self.max_free_spaces = free_spaces
        self.free_spaces = free_spaces
        self._update_value()
        self._set_positions()
        self._update_free_space()

    def value(self):
        return self.val

    def _update_value(self):
        self.val = sum([u.value() for u in self.units])

    def _set_positions(self):
        for i, u in enumerate(self.units):
            u.container_pos = i
            u.container = self

    def _update_free_space(self):
        needed = sum([u.size for u in self.units])
        if needed > self.max_free_spaces:
            raise ValueError('Container {0} is overflowing'.format(self))
        self.free_spaces = self.max_free_spaces - needed

    """ List-like interface """

    def remove(self, unit):
        if unit.container != self:
            raise ValueError('Unit is not in this container')
        del self[unit.container_pos]

    def append(self, unit):
        if self.free_spaces < unit.size:
            msg = "There is not enough space in this container for this unit"
            raise Exception(msg)
        unit.container_pos = len(self)
        unit.container = self
        self.units.append(unit)
        self.val += unit.value()
        self.free_spaces -= unit.size

    def extend(self, units):
        for unit in units:
            self.append(unit)

    def __iadd__(self, units):
        """ += operator """
        self.extend(units)
        return self

    def __len__(self):
        return len(self.units)

    def __getitem__(self, pos):
        return self.units[pos]

    def __setitem__(self, pos, unit):
        old = self.units[pos]
        if self.free_spaces + old.size < unit.size:
            msg = "There is not enough space in this container for this unit"
            raise Exception(msg)
        self.units[pos] = unit
        self.val += unit.value() - old.value()
        self.free_spaces += old.size - unit.size
        old.remove_from_container()
        unit.add_to_container(self, pos)

    def __delitem__(self, pos):
        self.units[pos].remove_from_container()
        self.free_spaces += self.units[pos].size
        self.val -= self.units[pos].value()
        del self.units[pos]
        for i, unit in enumerate(self.units[pos:]):
            unit.container_pos = pos + i

    def __iter__(self):
        return iter(self.units)


class Squad(Container):
    """contains a number of Units. Takes a list of Units"""
    def __init__(self, data=None, name=None, kind=None, element=None,
                 owner=None):
        super(Squad, self).__init__(data=data, free_spaces=8, owner=owner)
        self.name = name
        if data is None and kind == 'mins':
            self._fill_default_units(element, set_name=(name is None))
        self.stronghold = None
        self.stronghold_pos = None
        self.queued_field = None

    @property
    def owner(self):
        return self._owner

    @owner.setter
    def owner(self, owner):
        for u in self:
            u.owner = owner
        self._owner = owner

    def api_view(self):
        return dict(
            name=self.name, units=[u.uid for u in self.units],
            stronghold=getattr(self.stronghold, 'location', None),
            stronghold_pos=self.stronghold_pos,
            queued_field=getattr(self.queued_field, 'world_coord', None)
        )

    def combatant_view(self):
        return dict(name=self.name, owner=self.owner.uid,
                    units=[u.api_view() for u in self])

    def add_to_stronghold(self, stronghold, pos):
        if self.queued_field is not None:
            raise ValueError('Can\'t change queued squad\'s stronghold')
        self.stronghold = stronghold
        self.stronghold_pos = pos

    def remove_from_stronghold(self):
        if self.queued_field is not None:
            raise ValueError('Can\'t change queued squad\'s stronghold')
        self.stronghold = None
        self.stronghold_pos = None

    def queue_at(self, field):
        self.queued_field = field

    def unqueue(self):
        self.queued_field = None

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, name):
        if name is None:
            name = rand_string()
        validate_length(name, **SQUAD_NAME_LEN)
        self._name = name

    def hp(self):
        """Returns the total HP of the Squad."""
        return sum([unit.hp for unit in self])

    def _fill_default_units(self, element, set_name=False):
        if element is None:
            raise("Kind requires element from {0}.".format(ELEMENTS))
        # The code below creates 4 units of element with a comp
        # of (4,2,2,0). Each unit is equiped with a unique weapon.
        s = Stone()
        s[element] = 4
        s.set_opp(element, 0)
        s.set_orth(element, 2)
        for wep in WEP_LIST:
            scient = Scient(element, s)
            scient.equip(weapons[wep](element, Stone()))
            scient.name = "Ms. " + wep
            self.append(scient)
        if set_name:
            self.name = element + ' mins'

    def __repr__(self, more=None):
        """This could be done better..."""
        if more is None:
            fmt = "<Squad {name}, Value: {value}, Free spaces: {space}>"
            return fmt.format(name=self.name, value=self.val,
                              space=self.free_spaces)
        s = ['{0}: {1}'.format(i, t.name) for i, t in enumerate(self)]
        s = '\n'.join(s)
        fmt = ("<Squad {name}, Value: {value}, Free spaces: {space}> \n"
               "{names}")
        return fmt.format(name=self.name, value=self.val,
                          space=self.free_spaces, names=s)

    def __call__(self, more=None):
        return self.__repr__(more=more)

""" Squad helpers """


def rand_squad(owner=None, element=None, kind='Scient', max_value=255, size=8,
               equip=False):
    """Returns a Squad of five random Scients of element. Random element used
       if none given."""
    if element is None:
        element = rand_element()
    if kind == 'Scient':
        units = [rand_unit(element=element, kind=kind, max_value=max_value)
                 for _ in range(size)]
        squad = Squad(owner=owner, data=units)
    else:
        squad = Squad(owner=owner)
        while squad.free_spaces >= 2:
            squad.append(rand_unit(element=element, max_value=max_value))
        if squad.free_spaces == 1:
            squad.append(rand_unit(element=element, kind='Scient',
                                   max_value=max_value))
    if equip:
        for unit in squad:
            if isinstance(unit, Scient):
                wep = rand_weapon(element=element, max_value=unit.value() // 2)
                unit.equip(wep)
    return squad


def max_squad_by_value(value):
    """Takes an integer, ideally even because we round down, and returns a
    squad such that comp[element] == value, comp[orth] == value/2, comp[opp]
    == 0"""
    squad = Squad()
    value = value // 2  # more logical, really.
    half = value // 2
    for i in ELEMENTS:
        s = Stone()
        s[i] = value
        s[OPP[i]] = 0
        for o in ORTH[i]:
            s[o] = half
        squad.append(Scient(i, s))
    return squad
