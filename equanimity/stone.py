"""
stone.py

Created by AFD on 2013-08-05.
Copyright (c) 2013 A. Frederick Dudley. All rights reserved.
"""
from collections import Mapping
from persistent import Persistent
from const import ELEMENTS


class Stone(Persistent, Mapping):
    # Limit should be overwritten by classes that inherit from Stone.
    limit = {'Earth': 255, 'Fire': 255, 'Ice': 255, 'Wind': 255}

    def __init__(self, comp=None):
        Persistent.__init__(self)
        self.comp = {'Earth': 0, 'Fire': 0, 'Ice': 0, 'Wind': 0}
        if isinstance(comp, Stone):
            self.comp = comp.comp
        if comp is None:
            comp = self.comp
        else:
            iter(comp)
            if sorted(self.comp) == sorted(comp):
                self.comp = dict(comp)
            else:
                raise ValueError('Invalid comp: {0}'.format(comp))

    def imbue(self, stone):
        """adds the values of stone.comp to self.comp up to self.limit.
           leaves any remaining point in stone and returns stone."""
        # Type checking isn't really necessary...
        if not isinstance(stone, Stone):
            raise TypeError("Stone must be a Stone.")
        for s in ELEMENTS:
            if (self.comp[s] + stone[s]) <= self.limit[s]:
                self.comp[s] += stone[s]
                stone[s] = 0
            else:
                r = self.limit[s] - self.comp[s]
                stone[s] -= r
                self.comp[s] += r

        if stone.value() == 0:
            return
        else:
            return stone

    def split(self, comp):
        """subtracts comp from self, returns new stone"""
        if sum(comp.values()) > self.value():
            # > instead of >= for the silo case.
            raise ValueError("Sum of comp must be less than value of stone.")
        else:
            s = Stone()
            for e in ELEMENTS:
                if comp[e] > self.comp[e]:
                    raise ValueError("comp[{0}] cannot be greater than "
                                     "stone[{1}].".format(e, e))
                else:
                    self.comp[e] -= comp[e]
                    s[e] = comp[e]
        return s

    def tup(self):
        tup = ()
        for key in sorted(self.comp):
            tup += (self.comp[key],)
        return tup

    def value(self):
        return sum(self.comp.values())

    def __iter__(self):
        return iter(self.comp)

    def __contains__(self, value):
        return value in self.comp

    def __getitem__(self, key):
        return self.comp[key]

    def __setitem__(self, key, value):
        if value <= self.limit[key]:
            self.comp[key] = value
        else:
            err = "Tried setting {0} beyond its limit of {1}"
            raise AttributeError(err.format(key, str(self.limit[key])))

    def __len__(self):
        return len(self.comp)

    """
    __hash__ and __cmp__ are hacks to get around scients being mutable.
    I think the answer is to actually make stones immutable and
    have imbue return a different stone.
    """

    def __hash__(self):
        return id(self)
