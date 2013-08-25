from unittest import TestCase
from mock import MagicMock
from equanimity.grid import Grid
from equanimity.units import Scient, Nescient
from equanimity.unit_container import Squad
from equanimity.battlefield import Battlefield
from equanimity.const import E, F
from base import create_comp


class BattlefieldTest(TestCase):

    def test_create(self):
        bf = Battlefield()
        self.assertTrue(bf.grid)
        self.assertEqual(bf.graveyard, [])
        self.assertIs(bf.defsquad, None)
        self.assertIs(bf.atksquad, None)
        self.assertEqual(bf.dmg_queue, {})
        self.assertEqual(bf.squads, (None, None))
        self.assertEqual(bf.units, ())
        self.assertEqual(len(bf.direction), 6)
        self.assertEqual(len(bf.ranged), 5)
        self.assertEqual(len(bf.DOT), 5)
        self.assertEqual(len(bf.AOE), 5)
        self.assertEqual(len(bf.Full), 5)

    def test_create_with_grid(self):
        g = Grid()
        bf = Battlefield(grid=g)
        self.assertEqual(bf.grid, g)

    def test_create_with_defsquad(self):
        d = Squad()
        bf = Battlefield(defsquad=d)
        self.assertEqual(bf.defsquad, d)

    def test_create_with_atksquad(self):
        a = Squad()
        bf = Battlefield(atksquad=a)
        self.assertEqual(bf.atksquad, a)

    def test_get_units(self):
        dss = Scient(E, (20, 0, 0, 0))
        ass = Scient(F, (0, 20, 0, 0))
        dsq = Squad(name='def', data=[dss])
        asq = Squad(name='atk', data=[ass])
        bf = Battlefield(atksquad=asq, defsquad=dsq)
        self.assertEqual(bf.get_units(), (dss, ass))

    def test_on_grid(self):
        g = Grid(x=4, y=4)
        bf = Battlefield(grid=g)
        self.assertTrue(bf.on_grid((2, 3)))
        self.assertFalse(bf.on_grid((2, 10)))

    def test_get_adjacent(self):
        g = Grid(x=5, y=5)
        bf = Battlefield(grid=g)
        tiles = [(1, 3), (3, 3), (2, 2), (2, 4), (3, 2), (3, 4)]
        self.assertEqual(bf.get_adjacent((2, 3)), set(tiles))
        tiles = [(0, 1), (1, 0)]
        self.assertEqual(bf.get_adjacent((0, 0)), set(tiles))

    def test_make_parts(self):
        bf = Battlefield()
        body = bf.make_parts(dict(x='east', y='west'))
        for part in body.itervalues():
            self.assertIn(part.location, ['east', 'west'])

    def test_make_body(self):
        bf = Battlefield()
        body = bf.make_body((0, 0), 'North')
        print body
        keys = sorted(('tail', 'right', 'head', 'left'))
        self.assertEqual(sorted(body.keys()), keys)
        locs = [(-1, -1), (-1, 0), (0, 0), (-1, 1)]
        for i, k in enumerate(sorted(body.keys())):
            self.assertEqual(body[k].location, locs[i])
        body = bf.make_body((2, 3), 'North')
        print body
        self.assertEqual(sorted(body.keys()), keys)
        locs = [(2, 2), (1, 3), (2, 3), (2, 4)]
        for i, k in enumerate(sorted(body.keys())):
            self.assertEqual(body[k].location, locs[i])

    def test_body_on_grid(self):
        bf = Battlefield()
        body = bf.make_body((4, 4), 'North')
        self.assertTrue(bf.body_on_grid(body))
        for p in body.itervalues():
            p.location = map(lambda x: x - 200, p.location)
        self.assertFalse(bf.body_on_grid(body))

    def test_can_move_nescient(self):
        bf = Battlefield()
        body = bf.make_body((4, 4), 'North')
        nes = Nescient(E, create_comp(earth=128))
        self.assertTrue(bf.can_move_nescient(body, nes))
        x, y = body.values()[0].location
        bf.grid[x][y].contents = Scient(E, create_comp(earth=128))
        self.assertFalse(bf.can_move_nescient(body, nes))

    def test_move_nescient(self):
        bf = Battlefield()
        nes = Nescient(E, create_comp(earth=128))
        nes.take_body = MagicMock(side_effect=nes.take_body)
        body = bf.make_body((4, 4), 'North')
        self.assertTrue(bf.move_nescient(body, nes))
        nes.take_body.assert_called_with(body)
        self.assertEqual(nes.location, body['right'].location)

        # Blocked movement raises exception
        x, y = body.values()[0].location
        bf.grid[x][y].contents = Scient(E, create_comp(earth=128))
        self.assertRaises(ValueError, bf.move_nescient, body, nes)

    def test_place_nescient(self):
        bf = Battlefield()
        nes = Nescient(E, create_comp(earth=128))
        # Bad dest error
        dest = (-100, -100)
        self.assertRaises(ValueError, bf.place_nescient, nes, dest)

        # Body not on grid error
        dest = (0, 0)
        nes.facing = 'South'
        self.assertRaises(ValueError, bf.place_nescient, nes, dest)

        # Valid placement
        dest = (2, 2)
        self.assertTrue(bf.place_nescient(nes, dest))
