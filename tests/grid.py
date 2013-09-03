from unittest import TestCase
from equanimity.grid import Grid, Hex, Tile
from equanimity.const import E
from equanimity.stone import Stone
from base import create_comp


class TileTest(TestCase):

    def test_create(self):
        t = Tile(create_comp(earth=128))
        self.assertEqual(t.comp[E], 128)
        self.assertIs(t.contents, None)
        self.assertEqual(t.value(), 128)

    def test_create_with_contents(self):
        t = Tile(contents=1)
        self.assertEqual(t.contents, 1)
        self.assertEqual(t.value(), 0)


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


class HexGridTest(TestCase):

    def test_create(self):
        h = Grid()
        self.assertEqual(h.radius, 16)
        self.assertEqual(h.size, 817)
        self.assertEqual(len(list(h.iter_coords())), h.size)
        self.assertEqual(h._count_tiles(h.tiles), h.size)
        self.assertEqual(len(h.directions), 6)
        self.assertEqual(len(h.vectors), 6)

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

    def test_repr(self):
        h = Grid(radius=1)
        s = ("{0: {0: <Stone: Earth: 0, Fire: 0, Ice: 0, Wind: 0>, 1: <Stone: "
             "Earth: 0, Fire: 0, Ice: 0, Wind: 0>, -1: <Stone: Earth: 0, "
             "Fire: 0, Ice: 0, Wind: 0>}, 1: {0: <Stone: Earth: 0, Fire: 0, "
             "Ice: 0, Wind: 0>, -1: <Stone: Earth: 0, Fire: 0, Ice: 0, Wind: "
             "0>}, -1: {0: <Stone: Earth: 0, Fire: 0, Ice: 0, Wind: 0>, 1: "
             "<Stone: Earth: 0, Fire: 0, Ice: 0, Wind: 0>}}")
        self.assertEqual(s, repr(h))

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
        self.assertNotIn(None, h)

    def test_values(self):
        h = Grid(radius=2)
        self.assertEqual(h.tiles.values(), h.values())

    def test_items(self):
        h = Grid(radius=2)
        self.assertEqual(h.tiles.items(), h.items())

    def test_itervalues(self):
        h = Grid(radius=2)
        self.assertEqual(list(h.itervalues()), h.values())

    def test_iteritems(self):
        h = Grid(radius=2)
        self.assertEqual(list(h.iteritems()), h.items())

    def test_iter(self):
        h = Grid(radius=2)
        self.assertEqual(list(h), list(h.tiles))

    def test_in_bounds(self):
        h = Grid()
        for loc in h.iter_coords():
            self.assertTrue(h.in_bounds(loc))
