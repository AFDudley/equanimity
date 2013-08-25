"""
factory.py

Created by AFD on 2013-08-05.
Copyright (c) 2013 A. Frederick Dudley. All rights reserved.
"""
import persistent

from const import OPPSEX
from units import Scient, Nescient
from unit_container import Container
from weapons import Sword, Bow, Wand, Glove


class Factory(persistent.Persistent, Container):
    """contains a number of Units. Takes a list of Units"""
    def __init__(self, data=None):
        Container.__init__(self, data=None, free_spaces=1)
        self.produced = {}

    def __setitem__(self, key, val):
        Container.__setitem__(self, key, val)
        self.produced.update({key.id: False})

    def __delitem__(self, key):
        Container.__delitem__(self, key)
        del self.produced[key.id]

    def append(self, item):
        Container.append(self, item)
        self.produced.update({item.id: False})

    def upgrade(self):
        self.free_spaces += 1

    def reset(self):
        self.produced = {unit.id: False for unit in self.data}


class Stable(Factory):
    def __init__(self):
        super(Stable, self).__init__()
        self.kind = 'Stable'

    def __setitem__(self, key, val):
        if self.unit_size(val) == 2:
            super(Stable, self).__setitem__(key, val)
        else:
            raise Exception("Stables can only contain Nescients.")

    def append(self, item):
        if self.unit_size(item) == 2:
            super(Stable, self).append(item)
        else:
            raise Exception("Stables can only contain Nescients.")

    def produce(self, silo, season):
        """Produce one offspring 1/8th the comp of the parent."""
        # called everyday.
        nescient_list = []
        sexes = [unit.sex for unit in self.data]
        if len(self.data) > 1:  # It takes two to tango, baby.
            for unit in self.data:
                if unit.element == season:
                    if OPPSEX[unit.sex] in sexes:
                        if not self.produced[unit.id]:
                            c = {k: v/8 for k, v in unit.comp.iteritems()}
                            stone = silo.get(c)
                            nescient = Nescient(unit.element, stone)
                            nescient_list.append(nescient)
                            self.produced[unit.id] = True
                        else:
                            pass  # unit has already had a kid this year.
                    else:
                        pass  # need one of each sex.
            return nescient_list


class Armory(Factory):
    """Produces the 'best' weapon of unit's comp."""
    def __init__(self):
        Factory.__init__(self)
        self.kind = 'Armory'

    def produce(self, silo):
        #called every week?
        weapon_list = []
        for unit in self.data:
            if not self.produced[unit.id]:
                stone = silo.get(unit.comp)
                if unit.element == 'Earth':
                    weapon = Sword('Earth', stone)
                elif unit.element == 'Fire':
                    weapon = Bow('Fire', stone)
                elif unit.element == 'Ice':
                    weapon = Glove('Ice', stone)
                elif unit.element == 'Wind':
                    weapon = Wand('Wind', stone)
                weapon_list.append(weapon)
                self.produced[unit.id] = True
        return weapon_list


class Home(Factory):
    def __init__(self):
        super(Home, self).__init__()
        self.kind = 'Home'

    def __setitem__(self, key, val):
        if self.unit_size(val) == 1:
            super(Home, self).__setitem__(key, val)
        else:
            raise Exception("Homes can only contain Scients.")

    def append(self, item):
        if self.unit_size(item) == 1:
            super(Home, self).append(item)
        else:
            raise Exception("Homes can only contain Scients.")

    def produce(self, silo):
        #call once a year.
        scient_list = []
        sexes = [unit.sex for unit in self.data]
        if len(self.data) > 1:  # It takes two to tango, baby.
            for unit in self.data:
                if OPPSEX[unit.sex] in sexes:
                    if not self.produced[unit.id]:
                        c = {k: v / 8 for k, v in unit.comp.iteritems()}
                        stone = silo.get(c)
                        scient = Scient(unit.element, stone)
                        scient_list.append(scient)
                        self.produced[unit.id] = True
                    else:
                        pass  # unit has already had a kid this year.
                else:
                    pass  # need one of each sex.
            return scient_list


class Farm(Factory):
    """Planting is done in the field."""
    #called everyday
    def __init__(self):
        Factory.__init__(self)
        self.kind = 'Farm'

    def produce(self, tiles_comps):
        """returns True if all the stones can be planted."""
        #tiles_comps is a dict.
        #A tile_comp: {'(0, 0)': ({E:1,F:1,I:1,W:1}, 4)}
        size = 0
        workers = {}
        has_scient = False
        for unit in self.data:
            s = self.unit_size(unit)
            if s == 1:
                has_scient = True
            workers[unit.id] = s, unit.value()
            size += s
        if has_scient:
            if len(tiles_comps) > size:
                raise Exception("Tried planting too many stones.")
            else:
                #sort workers highest to lowest value.
                iv = [(k, v[1]) for k, v in workers.iteritems()]
                sorted_workers = sorted(iv, key=lambda tup: tup[1],
                                        reverse=True)

                #sort tiles_comps highest to lowest comp.
                sorted_tiles = sorted(tiles_comps.iteritems(),
                                      key=lambda tup: tup[1][1], reverse=True)
                for n in xrange(len(sorted_workers)):
                    #can the unit lift the stone?
                    if sorted_workers[n][1] < sorted_tiles[1][1]:
                        msg = "comp: {0} could not be planted."
                        raise Exception(msg.format(sorted_tiles[1][0]))
                return True
