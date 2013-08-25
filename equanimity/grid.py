"""
grid.py

Created by AFD on 2013-08-05.
Copyright (c) 2013 A. Frederick Dudley. All rights reserved.
"""
import random
from collections import namedtuple

from stone import Stone


class Loc(namedtuple('Loc', 'x y')):
    __slots__ = ()

    def __repr__(self):
        return '(%r, %r)' % self

noloc = Loc(None, None)


class Tile(Stone):
    """Tiles contain units or stones and are used to make battlefields."""
    #TODO consider removing contents.
    def __init__(self, comp=Stone(), contents=None):
        Stone.__init__(self, comp)
        self.contents = contents


class Grid(Stone):
    """A grid is a collection of tiles."""
    #NOTE: The comp that is provided during init is NOT the comp that is set
    # after init. The world should be the only thing creating Grids, so this
    # is less of an issue. A fix would be nice. TODO

    def calc_comp(self):
        """Calculates the comp based on ACTUAL tile values."""
        temp_comp = Stone().comp
        for x in xrange(self.x):
            for y in xrange(self.y):
                for suit, value in self.tiles[x][y].iteritems():
                    temp_comp[suit] += value
        for suit in temp_comp.keys():
            self.comp[suit] = temp_comp[suit] / (self.x * self.y)

    def __init__(self, comp=Stone(), x=16, y=16, tiles=None):
        Stone.__init__(self, comp)
        self.x, self.y = self.size = (x, y)
        if not self.value():
            if tiles is None:
                self.tiles = {}
                for i in range(x):
                    row = {}
                    for j in range(y):
                        row.update({j: Tile()})
                    self.tiles.update({i: row})
            else:
                for x in xrange(self.x):
                    for y in xrange(self.y):
                        for suit, value in tiles[x][y].iteritems():
                            self.comp[suit] += value
                for suit in self.comp.keys():
                    self.comp[suit] /= self.x * self.y
                self.tiles = tiles
        else:
            '''TODO: check for comp/tiles match. Currently assumes if comp,
            no tiles.'''
            #creates a pool of comp points to pull from.
            pool = {}
            for suit, value in self.comp.iteritems():
                pool[suit] = value * self.x * self.y
            #pulls comp points from the pool using basis and skew to
            # determine the range of random
            #values used to create tiles. Tiles are then shuffled.
            tiles_l = []
            for i in xrange(x-1):
                row_l = []
                for j in xrange(y):
                    """This is pretty close, needs tweeking."""
                    new_tile = Stone()
                    for suit, value in pool.iteritems():
                        '''This determines the range of the tile comps.'''
                        #good enough for the time being.
                        # this doesn't work as basis approaches limit:
                        basis = self.comp[suit]
                        skew = 2 * random.randint((basis / 4), (basis * 4))
                        pull = random.randint(0, min(self.limit[suit],
                                                     basis+skew))
                        nv = max(basis / 2, min(pull, self.limit[suit]))
                        #print "first nv: %s, pull: %s" % (nv, pull)
                        pool[suit] -= nv
                        new_tile[suit] = nv
                    row_l.append(new_tile)
                row = {}
                random.shuffle(row_l)  # shuffles tiles in temp. row.
                tiles_l.append(row_l)
            # special error correcting row (doesn't really work.)
            row_e = []
            for k in xrange(y):
                new_tile = Stone()
                for suit, value in pool.iteritems():
                    if pool[suit] != 0:
                        fract = pool[suit]/max(1, k)
                    else:
                        fract = 0
                    nv = max(basis/2, min(fract, self.limit[suit]))
                    #print "second nv: %s, fract: %s" % (nv, fract)
                    pool[suit] -= nv
                    new_tile[suit] = nv
                row_e.append(new_tile)
            # hacks upon hacks pt2
            del row_e[-1]
            half = {}
            for suit, value in row_e[-1].iteritems():
                half[suit] = int(value/2)
                row_e[-1][suit] -= half[suit]
            row_e.append(half)
            tiles_l.append(row_e)
            self.tiles = {}
            random.shuffle(tiles_l)  # shuffles temp rows.
            for x in xrange(self.x):
                row = {}
                for y in xrange(self.y):
                    # This shuffles the tiles before putting them in the grid.
                    # pick a row
                    r_index = random.choice(range(len(tiles_l)))
                    # pick a tile
                    c_index = random.choice(range(len(tiles_l[r_index])))
                    # place tile in grid
                    row.update({y: Tile(tiles_l[r_index][c_index])})
                    del tiles_l[r_index][c_index]  # remove used tile
                    if not len(tiles_l[r_index]):
                        # remove empty rows from tiles_l
                        del tiles_l[r_index]
                self.tiles.update({x: row})
            del tiles_l
            # Determine the actual comp NEEDS REAL SOLUTION TODO
            self.calc_comp()

    def imbue(self, stone):
        raise Exception("Cannot imbue Grid, use imbue_tile instead.")

    def imbue_tile(self, tileLoc, stone):
        """Imbues tile with stone, updates grid.comp."""
        self.tiles[tileLoc[0]][tileLoc[1]].imbue(stone)
        self.calc_comp()

    def __iter__(self):
        return iter(self.tiles)

    def __contains__(self, value):
        return value in self.tiles

    def __getitem__(self, key):
        return self.tiles[key]

    def __setitem__(self, key, value):
        self.tiles[key] = value

    def __len__(self):
        return len(self.tiles)

    def __repr__(self):
        return dict.__repr__(self.tiles)
