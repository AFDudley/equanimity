from unittest import TestCase
from equanimity.grid import Grid, Hex, Tile, HexCube
from equanimity.const import E
from equanimity.stone import Stone
from equanimity.units import Scient
from ..base import create_comp, FlaskTestDB


class TileTest(FlaskTestDB):

    def test_create(self):
        t = Tile()
        self.assertTrue(t.location.is_null())
        self.assertIs(t.contents, None)
        self.assertEqual(t.value(), 0)

    def test_create_with_location(self):
        loc = Hex(0, 1)
        t = Tile(location=loc)
        self.assertEqual(t.location, loc)

    def test_create_with_contents(self):
        s = Scient(E, create_comp(earth=128))
        t = Tile(contents=s)
        self.assertEqual(t.contents, s)
        self.assertEqual(t.value(), 0)

    def test_create_with_comp(self):
        t = Tile(comp=create_comp(earth=128))
        self.assertEqual(t.comp[E], 128)
        self.assertIs(t.contents, None)
        self.assertEqual(t.value(), 128)

    def test_equality(self):
        t = Tile((0, 1))
        self.assertEqual(t, Tile((0, 1)))
        self.assertNotEqual(t, Tile((1, 0)))
        self.assertNotEqual(t, (0, 1))

    def test_flush(self):
        s = Scient(E, create_comp(earth=128))
        loc = Hex(1, 2)
        t = Tile(loc, contents=s)
        self.assertEqual(t.contents, s)
        self.assertEqual(s.location, loc)
        self.assertTrue(t.flush())
        self.assertTrue(s.location.is_null())
        self.assertFalse(t.location.is_null())
        self.assertFalse(t.flush())

    def test_set_contents(self):
        t = Tile((0, 1))
        self.assertIs(t.contents, None)
        s = Scient(E, create_comp(earth=128))
        t.set_contents(s)
        self.assertEqual(t.contents, s)
        self.assertEqual(s.location, t.location)
        self.assertRaises(ValueError, t.set_contents, s)

    def test_move_contents_to(self):
        r = Scient(E, create_comp(earth=128))
        s = Scient(E, create_comp(earth=128))
        t = Tile((0, 1), contents=r)
        u = Tile((1, 0), contents=s)
        self.assertEqual(t.contents, r)
        self.assertEqual(u.contents, s)
        # t is same spot
        self.assertRaises(ValueError, t.move_contents_to, t)
        # u is occupied
        self.assertRaises(ValueError, t.move_contents_to, u)
        u.flush()
        self.assertIs(u.contents, None)
        self.assertTrue(s.location.is_null())
        t.move_contents_to(u)
        self.assertIs(t.contents, None)
        self.assertEqual(u.contents, r)
        self.assertEqual(r.location, u.location)
        t.flush()
        self.assertIs(t.contents, None)
        # t has nothing in it
        self.assertRaises(ValueError, t.move_contents_to, u)

    def test_occupied(self):
        t = Tile((0, 1))
        self.assertFalse(t.occupied())
        t.set_contents(Scient(E, create_comp(earth=128)))
        self.assertTrue(t.occupied())
        t.flush()
        self.assertFalse(t.occupied())


class HexTest(TestCase):

    def test_create(self):
        h = Hex(10, 15)
        self.assertEqual(h.q, 10)
        self.assertEqual(h.r, 15)
        self.assertEqual(h, (10, 15))

    def test_is_null(self):
        h = Hex(10, 15)
        self.assertFalse(h.is_null())
        h = Hex(None, None)
        self.assertTrue(h.is_null())
        h = Hex(10, None)
        self.assertTrue(h.is_null())
        h = Hex(None, 15)
        self.assertTrue(h.is_null())
        self.assertTrue(h.null.is_null())

    def test_from_cube(self):
        hc = HexCube(7, -2, 10)
        h = Hex.from_cube(hc)
        self.assertEqual(h.q, 7)
        self.assertEqual(h.r, 10)

    def test_arithmetic(self):
        h = Hex(2, 5)
        i = Hex(-1, 7)
        self.assertEqual(h - i, (3, -2))
        self.assertEqual(i - h, (-3, 2))
        self.assertEqual(h + i, (1, 12))
        self.assertEqual(i + h, (1, 12))


class HexCubeTest(TestCase):

    def test_create(self):
        h = HexCube(1, -1, 2)
        self.assertEqual(h.x, 1)
        self.assertEqual(h.y, -1)
        self.assertEqual(h.z, 2)
        self.assertEqual(h, (1, -1, 2))
        self.assertEqual(len(h.primaries), 6)
        self.assertEqual(len(h.nonprimaries), 6)
        for x in h.nonprimaries.itervalues():
            self.assertEqual(len(set(x)), 2)
        for d, x in h.primaries.iteritems():
            self.assertNotIn(x, h.nonprimaries[d])

    def test_from_hex(self):
        hex = Hex(1, -1)
        h = HexCube.from_hex(hex)
        self.assertEqual(h.x, 1)
        self.assertEqual(h.z, -1)
        self.assertEqual(h.y, 0)


class HexGridTest(FlaskTestDB):

    def test_create(self):
        h = Grid()
        self.assertEqual(h.radius, 8)
        self.assertEqual(h.size, 217)
        self.assertEqual(len(list(h.iter_coords())), h.size)
        self.assertEqual(h._count_tiles(h.tiles), h.size)
        self.assertEqual(len(h.directions), 6)
        self.assertEqual(len(h.vectors), 6)
        for t in h.iter_tiles():
            self.assertTrue(h.in_bounds(t.location))
        locs = [t.location for t in h.iter_tiles()]
        self.assertEqual(len(locs), len(set(locs)))
        for i, j in h.iter_coords():
            self.assertEqual(h[i][j].location, Hex(i, j))

    def test_create_with_comp(self):
        s = Stone(create_comp(earth=128))
        h = Grid(comp=s, radius=32)
        self.assertEqual(h._count_tiles(h.tiles), h.size)
        # average computed value should be close to the mean, as long
        # as the comp's values are not near limits (which will distort things)
        self.assertTrue(abs(h.comp[E] - s.comp[E]) < 8)

    def test_create_with_tiles(self):
        g = Grid(radius=2)
        tiles = {}
        for i, j in g.iter_coords():
            tiles.setdefault(i, {})[j] = Tile()
        h = Grid(radius=2, tiles=tiles)
        self.assertEqual(h.size, 19)
        self.assertEqual(tiles, h.tiles)

    def test_create_with_radius(self):
        h = Grid(radius=6)
        self.assertEqual(h.radius, 6)
        self.assertEqual(h.size, 127)
        self.assertEqual(h._count_tiles(h.tiles), h.size)

    def test_create_both_comp_and_tiles(self):
        self.assertRaises(ValueError, Grid, comp=Stone(), tiles=[])

    def test_create_not_enough_tiles(self):
        self.assertRaises(ValueError, Grid, radius=6,
                          tiles={0: {0: Tile()}})

    def test_create_bad_radius(self):
        self.assertRaises(ValueError, Grid, radius=0)
        self.assertRaises(ValueError, Grid, radius=-1)

    def test_get_adjacent(self):
        grid = Grid(radius=5)
        tiles = sorted([(1, 2), (0, 3), (2, 3), (1, 4), (2, 2), (0, 4)])
        self.assertEqual(sorted(list(grid.get_adjacent((1, 3)))), tiles)
        tiles = [(-5, 4), (-4, 5), (-4, 4)]
        self.assertEqual(grid.get_adjacent((-5, 5)), set(tiles))
        tiles = set([(-5, 4)])
        self.assertEqual(grid.get_adjacent((-5, 5), direction='North'), tiles)

    def test_get_direction(self):
        h = Grid()
        self.assertRaises(ValueError, h.get_direction, Hex(0, 0), Hex(0, 0))
        self.assertEqual(h.get_direction(Hex(-1, 0), Hex(2, -1)), 'Northeast')
        self.assertEqual(h.get_direction(Hex(-1, 0), Hex(2, 1)), 'Southeast')
        self.assertEqual(h.get_direction(Hex(-1, 0), Hex(-1, -2)), 'North')
        self.assertEqual(h.get_direction(Hex(-1, 0), Hex(-2, -2)), 'Northwest')
        self.assertEqual(h.get_direction(Hex(-1, 0), Hex(-3, -2)), 'Northwest')
        self.assertEqual(h.get_direction(Hex(-1, 0), Hex(-3, 2)), 'Southwest')
        self.assertEqual(h.get_direction(Hex(-1, 0), Hex(-1, -3)), 'North')
        self.assertEqual(h.get_direction(Hex(-1, 0), Hex(-1, 3)), 'South')
        self.assertEqual(h.get_direction(Hex(-1, 0), Hex(0, 3)), 'Southeast')
        self.assertEqual(h.get_direction(Hex(-1, 0), Hex(-2, 3)), 'South')

    def test_str(self):
        h = Grid(radius=1)
        s = ("{0: {0: {'comp': {'Fire': 0, 'Earth': 0, 'Wind': 0, 'Ice': 0}, "
             "'limit': {'Fire': 255, 'Earth': 255, 'Wind': 255, 'Ice': 255}}, "
             "1: {'comp': {'Fire': 0, 'Earth': 0, 'Wind': 0, 'Ice': 0}, "
             "'limit': {'Fire': 255, 'Earth': 255, 'Wind': 255, 'Ice': 255}}, "
             "-1: {'comp': {'Fire': 0, 'Earth': 0, 'Wind': 0, 'Ice': 0}, "
             "'limit': {'Fire': 255, 'Earth': 255, 'Wind': 255, 'Ice': 255}}},"
             " 1: {0: {'comp': {'Fire': 0, 'Earth': 0, 'Wind': 0, 'Ice': 0}, "
             "'limit': {'Fire': 255, 'Earth': 255, 'Wind': 255, 'Ice': 255}}, "
             "-1: {'comp': {'Fire': 0, 'Earth': 0, 'Wind': 0, 'Ice': 0}, "
             "'limit': {'Fire': 255, 'Earth': 255, 'Wind': 255, 'Ice': 255}}},"
             " -1: {0: {'comp': {'Fire': 0, 'Earth': 0, 'Wind': 0, 'Ice': 0}, "
             "'limit': {'Fire': 255, 'Earth': 255, 'Wind': 255, 'Ice': 255}}, "
             "1: {'comp': {'Fire': 0, 'Earth': 0, 'Wind': 0, 'Ice': 0}, "
             "'limit': {'Fire': 255, 'Earth': 255, 'Wind': 255, 'Ice': 255}}}}"
             "")
        self.assertEqual(s, str(h))

    def test_tiles_in_range(self):
        h = Grid()
        tiles = h.tiles_in_range((0, 0), 2)
        expected = h.get_adjacent((0, 0))
        adj = [h.get_adjacent(loc) for loc in expected]
        adj = reduce(lambda x, y: x | y, adj)
        expected |= adj
        expected -= set((Hex(0, 0),))
        self.assertEqual(tiles, expected)

    def test_len(self):
        h = Grid(radius=2)
        self.assertEqual(len(h), h.size)

    def test_delitem(self):
        h = Grid(radius=2)
        self.assertRaises(UserWarning, h.__delitem__, 0)

    def test_setitem_getitem(self):
        h = Grid(radius=2)
        h[0] = 'x'
        self.assertEqual(h.tiles[0], 'x')
        self.assertEqual(h[0], 'x')

    def test_contains(self):
        h = Grid(radius=2)
        t = h.get(Hex(0, 0))
        self.assertIn(t, h)
        self.assertFalse(t.location.is_null())
        self.assertEqual(t.location, Hex(0, 0))
        self.assertNotIn((-1000, -1000), h)

    def test_in_bounds(self):
        h = Grid()
        for loc in h.iter_coords():
            self.assertTrue(h.in_bounds(loc))

    def test_equality(self):
        h = Grid(radius=3)
        g = Grid(radius=2)
        self.assertNotEqual(h, g)
        self.assertEqual(h, h)
        self.assertEqual(h, Grid(radius=3))
        self.assertNotEqual(h, 1)

    def test_full(self):
        h = Grid(radius=1)
        self.assertFalse(h.full())
        for t in h.iter_tiles():
            t.set_contents(Scient(E, create_comp(earth=128)))
        self.assertTrue(h.full())

    def test_get_triangulating_vectors(self):
        h = Grid()
        for i in range(6):
            vecs = h.get_triangulating_vectors(h.directions[i])
            first = h.directions[i]
            second = h.directions[(i + 1) % 6]
            self.assertEqual(vecs, (h.vectors[first], h.vectors[second]))
