"""
stone.py

Created by AFD on 2013-08-05.
Copyright (c) 2013 A. Frederick Dudley. All rights reserved.
"""
from collections import Mapping
from persistent import Persistent
from const import ELEMENTS


class Component(dict):
    def __init__(self, value=None):
        """ All elements are set to value """
        _value = value
        if value is None:
            value = -1
        super(Component, self).__init__()
        for e in ELEMENTS:
            self[e] = value
        if _value is not None:
            self._sanity_check()

    @classmethod
    def create(cls, *args, **kwargs):
        """ A meta-create function that allows initialization of a
        Component in multiple ways

        e.g.
        Component({'Earth': 0, 'Wind': 100, 'Fire': 70, 'Ice': 0})
        Component((0, 100, 70, 0))
        Component(earth=0, wind=100, fire=70, ice=0)

        """
        if len(args) == 4:
            return cls.from_sequence(args)
        elif len(args) == 1:
            val = args[0]
            if isinstance(val, Mapping):
                return cls.from_dict(val)
            else:
                return cls.from_sequence(val)
        else:
            return cls.from_keys(**kwargs)

    @classmethod
    def from_keys(cls, earth=0, fire=0, ice=0, wind=0):
        """ Create using keyword arguments """
        c = cls()
        for e, v in zip(ELEMENTS, [earth, fire, ice, wind]):
            c[e] = v
        c._sanity_check()
        return c

    @classmethod
    def from_sequence(cls, tup):
        """ Create given an iterable """
        c = cls()
        for e, v in zip(ELEMENTS, tup):
            c[e] = v
        c._sanity_check()
        return c

    @classmethod
    def from_dict(cls, d):
        """ Create given a dict. The keys of the dict should match those in
        const.ELEMENTS """
        c = cls()
        c.update(d)
        c._sanity_check()
        return c

    def _sanity_check(self):
        for e in ELEMENTS:
            if self[e] < 0 or self[e] > 255:
                raise ValueError('Element {0} is {1}'.format(e, self[e]))


class Stone(Persistent, Mapping):
    # Limit should be overwritten by classes that inherit from Stone.
    def __init__(self, comp=None):
        Persistent.__init__(self)
        if comp is None:
            comp = Component(0)
        elif isinstance(comp, Stone):
            comp = comp.comp
        else:
            comp = Component.create(comp)
        self.comp = comp
        self.limit = Component(255)

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

        if stone.value():
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

    def __repr__(self):
        return '<Stone {comp}>'.format(comp=self.comp)

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
