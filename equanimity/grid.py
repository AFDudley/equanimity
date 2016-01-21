"""
grid.py

Created by AFD on 2013-08-05.
Copyright (c) 2013 A. Frederick Dudley. All rights reserved.
"""
import random
from bidict import bidict, inverted
from collections import namedtuple
from itertools import product, ifilter

from stone import Stone
from helpers import classproperty


class Tile(Stone):

    """Tiles contain units or stones and are used to make battlefields."""

    def __init__(self, location=None, comp=None, contents=None):
        super(Tile, self).__init__(comp=comp)
        if location is None:
            self.location = Hex.null
        else:
            self.location = Hex._make(location)
        self.contents = None
        if contents is not None:
            self.set_contents(contents)

    def __eq__(self, other):
        if not isinstance(other, Tile):
            return False
        return (self.location == other.location)

    def __ne__(self, other):
        return (not self.__eq__(other))

    def flush(self):
        if not self.occupied():
            return False
        self.contents.location = Hex.null
        self.contents = None
        return True

    def set_contents(self, contents):
        if self.occupied():
            raise ValueError('Tile {0} is not empty'.format(self))
        self.contents = contents
        contents.location = self.location

    def move_contents_to(self, dest):
        if self == dest:
            raise ValueError('Can\'t move to the same loc {0}'.format(self))
        if not self.occupied():
            raise ValueError('There is nothing at {0}'.format(self))
        dest.set_contents(self.contents)
        self.contents = None

    def occupied(self):
        return (self.contents is not None)


class Hex(namedtuple('Hex', 'q r')):
    __slots__ = ()

    @classmethod
    def from_cube(cls, hc):
        return cls(hc.x, hc.z)

    def is_null(self):
        return (None in self)

    def distance(self, other):
        other = self.__class__._make(other)
        return (abs(self.q - other.q) + abs(self.r - other.r)
                + abs(self.q + self.q - other.q - other.r)) / 2

    def __add__(self, other):
        other = self.__class__._make(other)
        return self.__class__(self.q + other.q, self.r + other.r)

    def __sub__(self, other):
        other = self.__class__._make(other)
        return self.__class__(self.q - other.q, self.r - other.r)


Hex.null = Hex(None, None)


class HexCube(namedtuple('HexCube', 'x y z')):
    __slots__ = ()

    # Primary sextant cube coordinates
    primaries = {
        'North': 'z',
        'Northeast': 'x',
        'Southeast': 'y',
        'South': 'z',
        'Southwest': 'x',
        'Northwest': 'y'
    }

    # Non-primary sextant cube coordinates
    nonprimaries = {
        'North': ['x', 'y'],
        'Northeast': ['y', 'z'],
        'Southeast': ['x', 'z'],
        'South': ['x', 'y'],
        'Southwest': ['y', 'z'],
        'Northwest': ['x', 'z'],
    }

    @classmethod
    def from_hex(cls, h):
        return cls(h.q, -h.q - h.r, h.r)


class Grid(Stone):

    """ Grid that uses axial/trapezoidal coordinate system outlined
    here: http://www.redblobgames.com/grids/hexagons/
    """

    _coords_cache = {}
    _inverted_vectors = None

    directions = bidict({
        0: 'North',
        1: 'Northeast',
        2: 'Southeast',
        3: 'South',
        4: 'Southwest',
        5: 'Northwest'
    })

    vectors = bidict({
        'North': Hex(0, -1),
        'Northeast': Hex(1, -1),
        'Southeast': Hex(1, 0),
        'South': Hex(0, 1),
        'Southwest': Hex(-1, 1),
        'Northwest': Hex(-1, 0)
    })

    @classproperty
    def inverted_vectors(cls):
        if cls._inverted_vectors is not None:
            return cls._inverted_vectors
        cls._inverted_vectors = bidict(inverted(cls.vectors))
        return cls._inverted_vectors

    @classmethod
    def is_adjacent(cls, q, r):
        """ Returns whether hex q is adjacent to hex r """
        q = Hex._make(q)
        r = Hex._make(r)
        return (q - r) in cls.inverted_vectors

    def __init__(self, comp=None, radius=2, tiles=None):
        if radius <= 0:
            raise ValueError('Invalid hex grid radius {0}'.format(radius))
        self.size = self.compute_size(radius)
        if comp is None:
            comp = Stone()
        else:
            if tiles is not None:
                raise ValueError('Tiles and comp are mutually exclusive')
            comp = Stone(comp)
        super(Grid, self).__init__(comp)
        self.radius = radius
        if comp.value:
            self._setup_tiles(comp)
        else:
            self._setup_fresh_tiles(tiles=tiles)
        self._update_comp_value()

    def get(self, (q, r)):
        if not self.in_bounds((q, r)):
            raise ValueError('{0} is out of bounds'.format((q, r)))
        return self.tiles[q][r]

    def get_direction(self, src, dest):
        """ Returns the direction the unit should face to aim at the unit.
        The destination will either be on the exact straight line along
        direction, or within the region triangulated by direction, and the
        direction to the right of direction.

        The branching logic is inferred from: http://i.imgur.com/cY9B0t7.png
        """
        if src == dest:
            raise ValueError('src {0} is dest'.format(src))
        # Get the point relative to the origin
        dest = dest - src
        # Convert to 3d coordinates
        d = HexCube.from_hex(dest)
        # Determine with sextant the point is in
        # North-Northeast:
        if d.z < 0 and d.x >= 0 and d.y > 0:
            return 'North'
        # Northeast-Southeast
        if d.x > 0 and d.y <= 0 and d.z < 0:
            return 'Northeast'
        # Southeast-South
        if d.y < 0 and d.x > 0 and d.z >= 0:
            return 'Southeast'
        # South-Southwest
        if d.z > 0 and d.x <= 0 and d.y < 0:
            return 'South'
        # Southwest-Northwest
        if d.x < 0 and d.y >= 0 and d.z > 0:
            return 'Southwest'
        # Northwest-North
        elif d.y > 0 and d.x < 0 and d.z <= 0:
            return 'Northwest'

    def get_adjacent(self, (q, r), direction='all', filtered=True):
        h = Hex(q, r)
        if direction == 'all':
            tiles = [h + v for v in self.inverted_vectors]
        else:
            tiles = [h + self.vectors[direction]]
        if filtered:
            return self.filter_tiles(tiles)
        else:
            return set(tiles)

    def get_triangulating_vectors(self, direction):
        """ Returns the vector for direction, and the vector for the direction
        next to it (to the right). These vectors can be used to triangulate
        the map """
        dirnum = self.directions[:direction]
        rightdir = self.directions[(dirnum + 1) % len(self.directions)]
        return (self.vectors[direction], self.vectors[rightdir])

    def tiles_in_range(self, location, distance):
        """generates a list of tiles within distance of location."""
        home = set([location])
        tilesets = [home]
        tiles = home
        union = lambda x, y: x | y
        for i in xrange(distance):
            adj = [self.get_adjacent(t, filtered=False) for t in tilesets[-1]]
            adj = reduce(union, adj)
            adj -= tiles
            tilesets.append(adj)
        return self.filter_tiles(reduce(union, tilesets[1:]))

    def filter_tiles(self, tiles):
        return set(filter(self.in_bounds, tiles))

    def full(self):
        return (not list(self.unoccupied_coords()))

    def in_bounds(self, (q, r)):
        vals = [q, r, q + r]
        return all(map(lambda x: -self.radius <= x <= self.radius, vals))

    def iter_coords(self):
        """ Returns a coord list iterator. There may be a way to do it without
        the filter but this has the desired result.
        Conceptually, it generates a square grid and discards the corner
        coordinates, leaving a hex map.
        """
        if self.radius not in self._coords_cache:
            span = xrange(-self.radius, self.radius + 1)
            self._coords_cache[self.radius] = filter(self.in_bounds,
                                                     product(span, span))
        return iter(self._coords_cache[self.radius])

    def placement_coords(self):
        """ Returns coords for one side of the field """
        return ifilter(lambda x: x[0] > 0, self.iter_coords())

    def occupied_coords(self):
        return (t.location for t in self.iter_tiles() if t.occupied())

    def unoccupied_coords(self):
        return (t.location for t in self.iter_tiles() if not t.occupied())

    def iter_tiles(self):
        for axis in self.tiles.itervalues():
            for tile in axis.itervalues():
                yield tile

    def __contains__(self, thing):
        loc = getattr(thing, 'location', thing)
        try:
            self.get(loc)
        except ValueError:
            return False
        return True

    def __getitem__(self, key):
        return self.tiles[key]

    def __setitem__(self, key, value):
        self.tiles[key] = value

    def __delitem__(self, key):
        raise UserWarning('__delitem__ not supported on Grid')

    def __len__(self):
        return self.size

    def __str__(self):
        return str(self.tiles)

    def __eq__(self, other):
        if not isinstance(other, self.__class__):
            return False
        return (list(self.iter_tiles()) == list(other.iter_tiles()))

    def __ne__(self, other):
        return (not self.__eq__(other))

    @classmethod
    def _triangulate(cls, n):
        # https://en.wikipedia.org/wiki/Triangular_number
        # Essentially a factorial for addition instead of multiplication
        return (n * (n + 1)) / 2

    @classmethod
    def compute_size(cls, radius):
        """ Computes number of tiles in a hex grid of radius N
        A hexagonal hex grid can be subdivided into 6 triangles, each of
        tile length radius-1, surrounding a single center tile
        """
        return cls._triangulate(radius) * 6 + 1

    def _setup_fresh_tiles(self, tiles=None):
        if tiles is None:
            tiles = {}
            for i, j in self.iter_coords():
                tiles.setdefault(i, {})[j] = Tile(Hex(i, j))
        else:
            if self._count_tiles(tiles) != self.size:
                msg = 'Need {0} tiles, only provided {1}'
                raise ValueError(msg.format(self.size, len(tiles)))
            for i, j in self.iter_coords():
                for suit, value in tiles[i][j].iteritems():
                    self.comp[suit] += value
            for suit in self.comp:
                self.comp[suit] /= self.size
        self.tiles = tiles

    def _setup_tiles(self, comp, stddev=64):
        '''
        Creates tiles with gaussian random values
        '''
        def random_tile(loc, stddev):
            s = Stone()
            for e, v in comp.iteritems():
                val = int(random.gauss(v, stddev))
                val = min(s.limit[e], s[e])
                val = max(0, s[e])
                s[e] = val
            return Tile(loc, comp=s)

        self.tiles = {}
        for i, j in self.iter_coords():
            self.tiles.setdefault(i, {})[j] = random_tile((i, j), stddev)

    def _update_comp_value(self):
        """ Sets self.comp to average of tiles' comps """
        c = Stone()
        for t in self.iter_tiles():
            for e, v in t.comp.iteritems():
                c[e] = v
        for e, v in c.iteritems():
            self.comp[e] = v / self.size

    def _count_tiles(self, tiles):
        return sum([len(row) for row in tiles.itervalues()])


class SquareGrid(Stone):

    """ Incomplete, but useful for testing since it is much quicker """

    def __init__(self, comp=None, radius=8, tiles=None):
        super(SquareGrid, self).__init__(comp)
        self.radius = radius

    def in_bounds(self, (x, y)):
        return (x >= 0 and x < self.radius and y >= 0 and y < self.radius)

    def iter_coords(self):
        return product(xrange(self.radius), xrange(self.radius))

    def get_adjacent(self, (x, y), direction='all', filtered=True):
        if direction == 'all':
            adj = [(x + 1, y + 1), (x + 1, y), (x + 1, y - 1), (x, y + 1),
                   (x, y - 1), (x - 1, y + 1), (x - 1, y), (x - 1, y - 1)]
        else:
            d = Grid.vectors[direction]
            adj = [(x + d.q, y + d.r)]
        adj = [Hex._make(a) for a in adj]
        if filtered:
            adj = filter(self.in_bounds, adj)
        return set(adj)
