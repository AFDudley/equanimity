"""
silo.py

Created by AFD on 2013-03-06.
Copyright (c) 2013 A. Frederick Dudley. All rights reserved.
"""

from stone import Stone
from transmuter import Transmuter


class Silo(Stone):
    """A silo is a really big stone that returns stones when requested."""

    def __init__(self, comp=None, limit=None):
        super(Silo, self).__init__(comp=comp, limit=limit)

    def get(self, comp):
        """Attempts to split the requsted stone,
        attempts transmuation if split fails."""
        return self.split(Transmuter(self.comp, comp).get_cost())

    def imbue_list(self, los):
        """surplus is destroyed."""
        for stone in los:
            self.imbue(stone)
