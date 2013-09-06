"""
unit_container.py

Created by AFD on 2013-03-06.
Copyright (c) 2013 A. Frederick Dudley. All rights reserved.
"""
import transaction
from persistent import Persistent
from persistent.list import PersistentList
import weapons
from stone import Stone
from const import ELEMENTS, WEP_LIST
from units import Scient
from player import WorldPlayer


class Container(Persistent):
    """contains units"""

    def __init__(self, data=None, free_spaces=8, owner=None):
        super(Container, self).__init__()
        self.owner = owner
        self.max_free_spaces = free_spaces
        self.free_spaces = free_spaces
        if data is None:
            self.units = PersistentList()
        elif isinstance(data, Stone):
            self.units = PersistentList(initlist=[data])
        else:
            self.units = PersistentList(initlist=data)
        self._update_value()
        self._set_positions()
        self._update_free_space()
        transaction.commit()

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
        old = self[pos]
        if self.free_spaces + old.size < unit.size:
            msg = "There is not enough space in this container for this unit"
            raise Exception(msg)
        self.units[pos] = unit
        self.val += unit.value() - old.value()
        self.free_spaces += old.size - unit.size
        old.container = None
        old.container_pos = None
        unit.container_pos = pos
        unit.container = self

    def __delitem__(self, pos):
        self.units[pos].container = None
        self.units[pos].container_pos = None
        self.free_spaces += self[pos].size
        self.val -= self[pos].value()
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
            self._fill_default_units(element)
        transaction.commit()

    def hp(self):
        """Returns the total HP of the Squad."""
        return sum([unit.hp for unit in self])

    def _fill_default_units(self, element):
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
            scient.equip(getattr(weapons, wep)(element, Stone()))
            scient.name = "Ms. " + wep
            self.append(scient)
        if self.name is None:
            self.name = element + ' mins'

    def __repr__(self, more=None):
        """This could be done better..."""
        if more is None:
            fmt = "Name: {name}, Value: {value}, Free spaces: {space} \n"
            return fmt.format(name=self.name, value=self.val,
                              space=self.free_spaces)
        s = ['{0}: {1}'.format(i, t.name) for i, t in enumerate(self)]
        s = '\n'.join(s)
        fmt = ("Name: {name}, Value: {value}, Free spaces: {space} \n"
               "{names}")
        return fmt.format(name=self.name, value=self.val,
                          space=self.free_spaces, names=s)

    def __call__(self, more=None):
        return self.__repr__(more=more)
