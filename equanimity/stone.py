"""
stone.py

Created by AFD on 2013-08-05.
Copyright (c) 2013 A. Frederick Dudley. All rights reserved.
"""
import random
from collections import Mapping
from persistent.mapping import PersistentMapping
from operator import itemgetter
from helpers import rand_element
from const import ELEMENTS, ORTH, OPP, KINDS


class Composition(dict):

    def __init__(self, value=None):
        """ All elements are set to value """
        _value = value
        if value is None:
            value = -1
        super(Composition, self).__init__()
        for e in ELEMENTS:
            self[e] = value
        if _value is not None:
            self.sanity_check()

    def orth(self, element):
        return [self[k] for k in ORTH[element]]

    def opp(self, element):
        return self[OPP[element]]

    def set_opp(self, element, val):
        self[OPP[element]] = val

    def set_orth(self, element, val):
        for el in ORTH[element]:
            self[el] = val

    @classmethod
    def create(cls, *args, **kwargs):
        """ A meta-create function that allows initialization of a
        Composition in multiple ways

        e.g.
        Composition({'Earth': 0, 'Wind': 100, 'Fire': 70, 'Ice': 0})
        Composition((0, 100, 70, 0))
        Composition(earth=0, wind=100, fire=70, ice=0)

        """
        if len(args) == 4:
            return cls.from_sequence(args)
        elif len(args) == 1:
            val = args[0]
            if hasattr(val, 'comp'):
                val = val.comp
            if isinstance(val, cls):
                c = Composition()
                c.update(val)
                return c
            elif isinstance(val, Mapping):
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
        c.sanity_check()
        return c

    @classmethod
    def from_sequence(cls, tup):
        """ Create given an iterable """
        c = cls()
        if len(tup) != len(ELEMENTS):
            raise ValueError('Missing or excessive elements: {0}'.format(tup))
        for e, v in zip(ELEMENTS, tup):
            c[e] = v
        c.sanity_check()
        return c

    @classmethod
    def from_dict(cls, d):
        """ Create given a dict. The keys of the dict should match those in
        const.ELEMENTS """
        if sorted(d.keys()) != sorted(ELEMENTS):
            raise ValueError('Invalid dict: {0}'.format(d))
        c = cls()
        c.update(d)
        c.sanity_check()
        return c

    def sanity_check(self):
        for e in ELEMENTS:
            if self[e] < 0 or self[e] > 255:
                raise ValueError('Element {0} is {1}'.format(e, self[e]))

    @property
    def value(self):
        return sum(self.values())

    def __str__(self):
        s = ['{0}: {1}'.format(e, self[e]) for e in ELEMENTS]
        return ', '.join(s)


class Stone(PersistentMapping):
    # Limit should be overwritten by classes that inherit from Stone.
    def __init__(self, comp=None, limit=None):
        super(Stone, self).__init__()
        if comp is None:
            comp = Composition(0)
        elif isinstance(comp, Stone):
            comp = comp.comp
        else:
            comp = Composition.create(comp)
        self.comp = comp
        if limit is None:
            limit = Composition(255)
        self.limit = limit

    def api_view(self):
        return dict(limit=self.limit, comp=self.comp)

    def copy(self):
        return Stone(comp=Composition.create(self.comp),
                     limit=Composition.create(self.limit))

    def imbue(self, stone):
        """adds the values of stone.comp to self.comp up to self.limit.
           leaves any remaining point in stone and returns stone."""
        # Type checking isn't really necessary...
        if not isinstance(stone, Stone):
            stone = Stone(Composition.create(stone))
        for s in ELEMENTS:
            if (self.comp[s] + stone[s]) <= self.limit[s]:
                self.comp[s] += stone[s]
                stone[s] = 0
            else:
                r = self.limit[s] - self.comp[s]
                stone[s] -= r
                self.comp[s] += r

        if stone.value:
            return stone

    def split(self, comp):
        """subtracts comp from self, returns new stone"""
        s = Stone()
        for e in ELEMENTS:
            if comp[e] > self.comp[e]:
                raise ValueError("comp[{0}] cannot be greater than "
                                 "stone[{1}].".format(e, e))
            else:
                self.comp[e] -= comp[e]
                s[e] = comp[e]
        return s

    def extract_award(self):
        s = self.copy()
        for e in self.comp.iterkeys():
            s[e] = self[e] // 2
            self[e] -= s[e]
        return s

    """ TODO (steve) -- merge stone & comp ? """

    def orth(self, element):
        return self.comp.orth(element)

    def opp(self, element):
        return self.comp.opp(element)

    def set_opp(self, element, val):
        return self.comp.set_opp(element, val)

    def set_orth(self, element, val):
        return self.comp.set_orth(element, val)

    def tup(self):
        tup = ()
        for key in sorted(self.comp):
            tup += (self.comp[key],)
        return tup

    @property
    def value(self):
        return self.comp.value

    def __str__(self):
        return '<Stone: {comp}>'.format(comp=self.comp)

    def __repr__(self):
        data = dict(comp=self.comp, limit=self.limit)
        return repr(data)

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

    def __hash__(self):
        return id(self)

    def __cmp__(self, other):
        a = self.value
        b = other.value
        if a < b:
            return -1
        elif a > b:
            return 1
        else:
            return 0


""" Stone/Comp helpers """


def t2c(tup):
    """Converts a tuple to a comp"""
    if len(tup) != 4:
        raise Exception("Incorrect number of values in tuple")
    comp = Stone()
    for i in range(4):
        comp[ELEMENTS[i]] = tup[i]
    return comp


def get_element(comp):
    """Gets the primary element from a comp, or choses at random from equals.
    """
    sort = sorted(comp.iteritems(), key=itemgetter(1), reverse=True)
    if sort[0][1] == sort[3][1]:  # they are all equal
        return random.choice(sort)[0]
    elif sort[0][1] == sort[2][1]:
        return random.choice(sort[:3])[0]
    elif sort[0][1] == sort[1][1]:
        return random.choice(sort[:2])[0]
    else:
        return sort[0][0]


def max_comp(element, kind='Scient'):
    """Returns the maximum composition of 'kind' of element 'element'"""
    comp = Stone()
    if kind == 'Scient':
        comp[element] = 255
        comp[OPP[element]] = 0
        comp[ORTH[element][0]] = comp[ORTH[element][1]] = 127
        return comp
    if kind == 'Weapon':
        comp2 = Stone()
        comp2[element] = comp[element] = 63
        comp2[OPP[element]] = comp[OPP[element]] = 0
        comp2[ORTH[element][0]] = comp[ORTH[element][1]] = 0
        comp2[ORTH[element][1]] = comp[ORTH[element][0]] = 63
        return (comp, comp2)
    if kind == 'Nescient':
        comp2 = Stone()
        comp2[element] = comp[element] = 255
        comp2[OPP[element]] = comp[OPP[element]] = 0
        comp2[ORTH[element][0]] = comp[ORTH[element][1]] = 0
        comp2[ORTH[element][1]] = comp[ORTH[element][0]] = 254
        return (comp, comp2)
    if kind == 'Stone':
        for i in comp:
            comp[i] = 255
        return comp


def rand_comp(element=None, kind=None, max_value=255):
    """Returns a random comp in 'element' for use instaniating 'kind'
       If 'element' is not valid, random element used.
       If 'kind' is not valid stone is used
       if 'kind' is 'Stone' element ignored"""
    if element is None:
        element = rand_element()
    if element not in ELEMENTS:
        raise ValueError('Unknown element {0}'.format(element))

    comp = Stone()
    if kind is None:
        kind = 'Stone'
    if kind not in KINDS:
        raise ValueError('Unknown kind {0}'.format(kind))

    if kind == 'Stone':
        for element in comp:
            comp[element] = random.randint(0, max_value)
        return comp
    elif kind == 'Scient':
        comp[element] = random.randint(1, max_value)
        for picked in ORTH[element]:
            # NOTE: if comp[element] = 1 orths will be 0.
            comp[picked] = random.randint(0, (comp[element] // 2))
        return comp
    elif kind == 'Nescient':
        comp[element] = random.randint(1, max_value)
        orth = random.choice(ORTH[element])
        comp[orth] = random.randint(1, comp[element])
        return comp
    elif kind == 'Weapon':
        pass
    else:
        raise NotImplementedError('Unimplement kind {0}'.format(kind))
