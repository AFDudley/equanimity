"""
silo.py

Created by AFD on 2013-03-06.
Copyright (c) 2013 A. Frederick Dudley. All rights reserved.
"""
import transaction

from stone import Stone, Composition
from transmuter import Transmuter


class Silo(Stone):
    """A silo is a really big stone that returns stones when requested."""

    def __init__(self, limit=None):
        Stone.__init__(self)
        #the limit will be set to 1.5 times a years harvest.
        if limit is not None:
            self.set_limit(self, limit)

    def set_limit(self, limit):
        self.limit.update(limit)
        transaction.commit()

    def transmute(self, comp):
        """attempts to transmute existing points into Stone of requested comp.
        """
        self.split(Transmuter(self.comp, comp).get_split())
        transaction.commit()
        return Stone(comp)

    def get(self, comp):
        """Attempts to split the requsted stone,
        attempts transmuation if split fails."""
        #WARNING: Transmutation checks are incomplete/suboptimal.
        comp = Composition.create(comp)
        if (sum(comp.values()) * 4) > self.value():
            msg = ("There are not enough points in the silo to create a stone "
                   "of {0}")
            raise ValueError(msg.format(comp))
        else:
            can_split = True
            for k in self.keys():
                if self[k] < comp[k]:
                    can_split = False
            if can_split:
                return self.split(comp)
            else:
                self.split(self.transmute(comp))
                return comp

    def imbue_list(self, los):
        """surplus is destroyed."""
        for stone in los:
            self.imbue(stone)
