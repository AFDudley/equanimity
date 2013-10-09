"""
silo.py

Created by AFD on 2013-03-06.
Copyright (c) 2013 A. Frederick Dudley. All rights reserved.
"""

from stone import Stone, Composition
from const import ELEMENTS
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

    def get(self, comp):
        """Attempts to split the requsted stone,
        attempts transmuation if split fails."""
        comp = Composition.create(comp)
        try:
            return self.split(comp)
        except ValueError:
            return self.split(Transmuter(self.comp, comp).get_split())

    def imbue_list(self, los):
        """surplus is destroyed."""
        for stone in los:
            self.imbue(stone)
