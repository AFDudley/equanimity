"""
units.py

Created by AFD on 2013-08-05.
Copyright (c) 2013 A. Frederick Dudley. All rights reserved.
"""
from datetime import datetime
from stone import Stone, Composition
from const import ELEMENTS, E, F, I, W, ORTH, OPP


class Unit(Stone):
    attrs = ['p', 'm', 'atk', 'defe', 'pdef', 'patk', 'mdef', 'matk', 'hp']

    def __init__(self, element, comp, name=None, location=None, sex='female'):
        if not element in ELEMENTS:
            fmt = "Invalid element: {0}, valid elements are {1}"
            raise Exception(fmt.format(element, ELEMENTS))
        if comp[element] == 0:
            raise ValueError("Units' primary element must be greater than 0.")

        if comp[OPP[element]] != 0:
            raise ValueError("Units' opposite element must equal 0.")

        super(Unit, self).__init__(comp)
        now = datetime.utcnow()
        self.element = element
        if name is None:
            name = str(hash(self))
        self.name = name
        self.location = location
        self.container = None
        self.sex = sex
        self.DOB = now
        self.DOD = None
        self.fed_on = None
        self.val = self.value()
        self.id = id(self)

    def calcstats(self):
        self.p = (2 * (self.comp[F] + self.comp[E]) + self.comp[I] +
                  self.comp[W])
        self.m = (2 * (self.comp[I] + self.comp[W]) + self.comp[F] +
                  self.comp[E])
        self.atk = (2 * (self.comp[F] + self.comp[I]) + self.comp[E] +
                    self.comp[W]) + (2 * self.value())
        self.defe = (2 * (self.comp[E] + self.comp[W]) + self.comp[F] +
                     self.comp[I])

        self.pdef = self.p + self.defe + (2 * self.comp[E])
        self.patk = self.p + self.atk + (2 * self.comp[F])
        self.matk = self.m + self.atk + (2 * self.comp[I])
        self.mdef = self.m + self.defe + (2 * self.comp[W])
        #does this make sense? It was wrong for a long time.
        self.hp = 4 * ((self.pdef + self.mdef) + self.value())

    def stats(self):
        return dict(zip(self.attrs, [getattr(self, s) for s in self.attrs]))

    def __repr__(self):
        return self.name


class Scient(Unit):
    """A Scient (playable character) unit.

    Initializer takes element and comp:
      * element - this unit's element (E, F, I, or W) aka 'suit'
      * comp - dictionary of this unit's composition on (0..255) {E: earth,
      F: fire, I: ice, W: wind}
    """

    def __init__(self, element, comp, name=None, weapon=None,
                 weapon_bonus=None, location=None, sex='female'):
        comp = Composition.create(comp)
        for o in comp.orth(element):
            if o > comp[element] / 2:
                raise ValueError("Scients' orthogonal elements cannot be "
                                 "more than half the primary element's "
                                 "value.")
        super(Scient, self).__init__(element, comp, name, location, sex)
        self.move = 4
        self.weapon = weapon
        if weapon_bonus is None:
            self.weapon_bonus = Stone()
        else:
            self.weapon_bonus = weapon_bonus
        self.equip_limit = Stone({E: 1, F: 1, I: 1, W: 1})
        for element in ELEMENTS:
            self.equip_limit.limit[element] = 256
        for i in self.equip_limit:
            self.equip_limit[i] = (self.equip_limit[i] + self.comp[i] +
                                   self.weapon_bonus[i])
        self.calcstats()

        #equiping weapons should be done someplace else.
        self.equip(self.weapon)

    def imbue(self, stone):
        """add stone to scient's comp, if legal"""
        comp = stone.comp
        if comp[OPP[self.element]] != 0:
            raise Exception("Primary element of stone must match that of "
                            "scient")
        for orth in ORTH[self.element]:
            if (comp[orth] + self.comp[orth] >
                    comp[self.element] + (self.comp[self.element] / 2)):
                raise ValueError("Scients' orthogonal elements cannot be"
                                 "more than half the primary element's "
                                 "value.")
        return super(Scient, self).imbue(stone)

    def equip(self, weapon):
        self.weapon = weapon

    def unequip(self):
        """removes weapon from scient, returns weapon."""
        weapon = self.weapon
        self.weapon = None
        return weapon


class Nescient(Unit):
    """A non-playable unit."""

    def __init__(self, element, comp, name=None, weapon=None,
                 location=None, sex='female', facing=None,
                 body=None):
        if body is None:
            body = {'head':  None, 'left': None, 'right': None, 'tail': None}
        comp = Stone(comp)
        orth = comp.orth(element)
        if all(orth):
            raise ValueError("Nescients' cannot have values greater than zero "
                             "for both orthogonal elements.")
        for o in orth:
            if o > comp[element]:
                raise ValueError("Nescients' orthogonal value cannot exceed "
                                 "the primary element value.")

        super(Nescient, self).__init__(element, comp, name, location, sex)
        self.move = 4
        #Set nescient type.
        if self.element == 'Earth':
            self.kind = 'p'
            if self.comp[F] == 0:
                self.type = 'Avalanche'  # AOE Full
            else:
                self.type = 'Magma'  # ranged Full

        elif self.element == 'Fire':
            self.kind = 'p'
            if self.comp[E] == 0:
                self.type = 'Firestorm'  # ranged DOT
                self.time = 3
            else:
                self.type = 'Forestfire'  # ranged Full

        elif self.element == 'Ice':
            self.kind = 'm'
            if self.comp[E] == 0:
                self.type = 'Icestorm'  # AOE DOT
                self.time = 3
            else:
                self.type = 'Permafrost'  # AOE Full
        else:  # Wind
            self.kind = 'm'
            self.time = 3
            if self.comp[F] == 0:
                self.type = 'Blizzard'  # AOE DOT
            else:
                self.type = 'Pyrocumulus'  # ranged DOT

        self.calcstats()
        for part in body:  # MESSY!!!!
            body[part] = Part(self)
        self.body = body
        self.location = location  # ...
        self.facing = facing
        self.weapon = self  # hack for attack logic.

    def take_body(self, new_body):
        """Takes locations from new_body and applies them to body."""
        for part in new_body:
            new_body[part].nescient = self
            self.body = new_body

    def calcstats(self):
        super(Nescient, self).calcstats()
        self.atk = (2 * (self.comp[F] + self.comp[I]) + self.comp[E] +
                    self.comp[W]) + (4 * self.value())
        self.hp = self.hp * 4  # This is an open question.


class Part(object):

    def __init__(self, nescient, location=None):
        self.nescient = nescient
        self.location = location

    @property
    def hp(self):
        return self.nescient.hp

    @hp.setter
    def hp(self, hp):
        self.nescient.hp = hp

    def __repr__(self):
        s = '<{0}: {1} [{2}]>'
        return s.format(self.__class__.__name__, self.location, self.nescient)
