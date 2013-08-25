"""
unit_container.py

Created by AFD on 2013-03-06.
Copyright (c) 2013 A. Frederick Dudley. All rights reserved.
"""
from UserList import UserList
import weapons
from stone import Stone
from const import ELEMENTS, OPP, ORTH, WEP_LIST
from units import Unit, Scient


class Container(UserList):
    """contains units"""

    def __init__(self, data=None, free_spaces=8):
        super(Container, self).__init__()
        self.val = 0
        self.free_spaces = free_spaces

    def unit_size(self, obj):
        if not isinstance(obj, Unit):
            raise TypeError("Containers are only for Units")
        else:
            if isinstance(obj, Scient):
                return 1
            else:
                return 2

    def append(self, item):
        size = self.unit_size(item)
        if self.free_spaces < size:
            msg = "There is not enough space in this container for this unit"
            raise Exception(msg)
        self.data.append(item)
        self.val += item.value()
        self.free_spaces -= size
        item.container = self

    def update_value(self):
        new_val = 0
        for u in self.data:
            new_val += u.value()
        self.val = new_val

    def value(self):
        return self.val

    def __setitem__(self, key, val):
        old = self[key]
        old_size = self.unit_size(old)
        size = self.unit_size(val)
        if self.free_spaces + old_size < size:
            msg = "There is not enough space in this container for this unit"
            raise Exception(msg)
        super(Container, self).__setitem__(key, val)
        self.val += val.value() - old.value()
        self.free_spaces += old_size - size
        val.container = self
        old.container = None

    def __delitem__(self, key):
        self.data[key].container = None
        temp = self[key].value()
        self.free_spaces += self.unit_size(self[key])
        self.data.__delitem__(key)
        self.val -= temp


class Squad(Container):
    """contains a number of Units. Takes a list of Units"""
    def __init__(self, data=None, name=None, kind=None, element=None):
        super(Squad, self).__init__(data=None, free_spaces=8)
        self.name = name
        if data is None:
            # The code below creates 4 units of element with a comp
            # of (4,2,2,0). Each unit is equiped with a unique weapon.
            if kind == 'mins':
                if element is None:
                    raise("Kind requires element from {0}.".format(ELEMENTS))
                else:
                    s = Stone()
                    s[element] = 4
                    s[OPP[element]] = 0
                    for o in ORTH[element]:
                        s[o] = 2
                    for wep in WEP_LIST:
                        scient = Scient(element, s)
                        scient.equip(getattr(weapons, wep)(element, Stone()))
                        scient.name = "Ms. " + wep
                        self.append(scient)
                if self.name is None:
                    self.name = element + ' mins'
            return

        if isinstance(data, list):
            for x in data:
                self.append(x)
        else:
            self.append(data)

    def hp(self):
        """Returns the total HP of the Squad."""
        return sum([unit.hp for unit in self])

    def __repr__(self, more=None):
        """This could be done better..."""
        if more is None:
            fmt = "Name: {name}, Value: {value}, Free spaces: {space} \n"
            return fmt.format(name=self.name, value=self.val,
                              space=self.free_spaces)
        else:
            s = ['{0}: {1}'.format(i, t.name) for i, t in enumerate(self)]
            s = '\n'.join(s)
            fmt = ("Name: {name}, Value: {value}, Free spaces: {space} \n"
                   "{names}")
            return fmt.format(name=self.name, value=self.val,
                              space=self.free_spaces, names=s)

    def __call__(self, more=None):
        return self.__repr__(more=more)
