from unittest import TestCase
from mock import MagicMock, patch
from equanimity.grid import Grid, Loc
from equanimity.units import Scient, Nescient
from equanimity.unit_container import Squad
from equanimity.battlefield import Battlefield
from equanimity.stone import Stone
from equanimity.const import E, F
from equanimity.weapons import Sword, Wand, Bow, Glove
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
        keys = sorted(('tail', 'right', 'head', 'left'))
        self.assertEqual(sorted(body.keys()), keys)
        locs = [(-1, -1), (-1, 0), (0, 0), (-1, 1)]
        for i, k in enumerate(sorted(body.keys())):
            self.assertEqual(body[k].location, locs[i])
        body = bf.make_body((2, 3), 'North')
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

        # blocked movement
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

    def test_get_rotations(self):
        # Test unable to move at all
        g = Grid(x=1, y=1)
        bf = Battlefield(grid=g)
        nes = Nescient(E, create_comp(earth=128))
        nes.body = bf.make_body((0, 0), 'North')
        self.assertFalse(bf.get_rotations(nes))

        bf = Battlefield()
        nes = Nescient(E, create_comp(earth=128))
        nes.body = bf.make_body((4, 4), 'North')
        dirs = sorted(bf.direction.values())
        self.assertEqual(sorted(bf.get_rotations(nes)), dirs)

    def test_rotate(self):
        bf = Battlefield()
        nes = Nescient(E, create_comp(earth=128))
        nes.body = bf.make_body((4, 4), 'North')
        self.assertTrue(bf.rotate(nes, 'Northeast'))
        self.assertEqual(nes.facing, 'Northeast')

        nes.body = bf.make_body((0, 0), 'North')
        self.assertRaises(ValueError, bf.rotate, nes, 'South')

    def test_make_triangle(self):
        bf = Battlefield()
        expect = [(3, 3), (4, 3), (4, 2), (3, 2), (5, 2)]
        got = bf.make_triangle((4, 4), 3, 'North')
        self.assertEqual(sorted(got), sorted(expect))

    def test_map_to_grid(self):
        bf = Battlefield()
        expect = [
            (5, 9), (6, 9), (9, 1), (7, 12), (9, 8), (8, 0), (3, 11), (0, 7),
            (11, 3), (8, 9), (4, 12), (0, 10), (9, 4), (6, 12), (7, 11),
            (2, 10), (1, 11), (8, 5), (10, 4), (10, 8), (9, 0), (4, 9), (2, 9),
            (11, 5), (10, 7), (10, 3), (3, 10), (6, 10), (7, 0), (8, 10),
            (0, 0), (5, 12), (0, 11), (8, 8), (7, 10), (1, 10), (8, 6), (7, 7),
            (10, 1), (11, 2), (9, 7), (4, 10), (10, 6), (11, 4), (8, 2),
            (5, 11), (6, 11), (8, 11), (9, 3), (10, 5), (7, 1), (0, 12),
            (9, 10), (3, 9), (1, 9), (8, 7), (10, 0), (5, 10), (1, 0), (0, 8),
            (9, 6), (4, 11), (7, 9), (0, 1), (8, 3), (8, 1), (3, 12), (1, 12),
            (8, 12), (9, 2), (2, 11), (9, 9), (0, 6), (1, 8), (12, 4), (0, 9),
            (9, 5), (10, 2), (7, 8), (0, 2), (11, 6), (2, 12)
        ]
        got = bf.map_to_grid((4, 4), Wand(E, create_comp(earth=128)))
        self.assertEqual(sorted(expect), sorted(got))
        expect = [(5, 4), (3, 3), (4, 5), (4, 3), (3, 4), (3, 5)]
        got = bf.map_to_grid((4, 4), Sword(E, create_comp(earth=128)))
        self.assertEqual(sorted(expect), sorted(got))

    def test_place_object(self):
        bf = Battlefield()
        # bad obj
        self.assertRaises(TypeError, bf.place_object, None, (0, 0))
        # scient placement
        self.assertTrue(bf.place_object(Scient(E, create_comp(earth=128)),
                                        (0, 1)))
        # nescient placement
        self.assertTrue(bf.place_object(Nescient(E, create_comp(earth=128)),
                                        (4, 4)))
        # stone placement
        self.assertTrue(bf.place_object(Stone(create_comp(earth=128)), (0, 3)))

    def test_move_scient(self):
        bf = Battlefield()
        # bad src
        self.assertRaises(ValueError, bf.move_scient, (-100, -100), (0, 0))
        # bad dest
        self.assertRaises(ValueError, bf.move_scient, (0, 0), (-100, -100))
        # nothing at src
        self.assertRaises(ValueError, bf.move_scient, (0, 0), (1, 1))
        # same spot
        self.assertRaises(ValueError, bf.move_scient, (0, 0), (0, 0))
        # something at dest
        s = Scient(E, create_comp(earth=128))
        bf.grid[0][0].contents = s
        bf.grid[2][2].contents = Scient(E, create_comp(earth=128))
        self.assertRaises(ValueError, bf.move_scient, (0, 0), (2, 2))
        # moving too far
        self.assertRaises(ValueError, bf.move_scient, (0, 0), (15, 15))

        # Valid move
        self.assertEqual(bf.grid[0][0].contents, s)
        self.assertTrue(bf.move_scient((0, 0), (1, 1)))
        self.assertIs(bf.grid[0][0].contents, None)
        self.assertEqual(bf.grid[1][1].contents, s)
        self.assertEqual(s.location, Loc(1, 1))

    def test_place_scient(self):
        bf = Battlefield()
        s = Scient(E, create_comp(earth=128))
        # placing off grid
        self.assertRaises(ValueError, bf.place_scient, s, (-100, -100))
        # valid placement
        self.assertTrue(bf.place_scient(s, (0, 0)))
        self.assertEqual(bf.grid[0][0].contents, s)
        self.assertEqual(s.location, Loc(0, 0))
        self.assertEqual(bf.dmg_queue[s], [])
        # re-placing in same spot
        self.assertRaises(ValueError, bf.place_scient, s, (0, 0))
        # placing in occupied spot
        t = Scient(E, create_comp(earth=128))
        self.assertRaises(ValueError, bf.place_scient, t, (0, 0))
        # placing as movement
        bf.move_scient = MagicMock(side_effect=bf.move_scient)
        self.assertTrue(bf.place_scient(s, (1, 1)))
        self.assertEqual(s.location, Loc(1, 1))
        bf.move_scient.assert_called_with(Loc(0, 0), Loc(1, 1))

    def test_find_units(self):
        bf = Battlefield()
        bf.place_object(Scient(E, create_comp(earth=128)), (0, 0))
        bf.place_object(Scient(E, create_comp(earth=128)), (2, 2))
        self.assertEqual(bf.find_units(), [(0, 0), (2, 2)])

    @patch('equanimity.battlefield.random.randint')
    def test_rand_place_scient(self, mock_randint):
        seq = [0] * 1000
        seq[5] = 1
        mock_randint.side_effect = iter(seq)
        g = Grid(x=2, y=2)
        bf = Battlefield(grid=g)
        s = Scient(E, create_comp(earth=128))
        self.assertTrue(bf.rand_place_scient(s))
        # this one will cause a ValueError to be caught because we mocked
        # it to return the same 0,0 position the first time
        s = Scient(E, create_comp(earth=128))
        self.assertTrue(bf.rand_place_scient(s))
        bf.place_object(Scient(E, create_comp(earth=128)), (1, 1))
        bf.place_object(Scient(E, create_comp(earth=128)), (1, 0))
        # error when full
        self.assertRaises(ValueError, bf.rand_place_scient, s)

    def test_rand_place_squad(self):
        bf = Battlefield()
        s = Scient(E, create_comp(earth=128))
        t = Scient(E, create_comp(earth=128))
        squad = Squad(name='xxx', data=[s, t])
        bf.rand_place_squad(squad)
        self.assertEqual(len(bf.find_units()), 2)

    def test_flush_units(self):
        bf = Battlefield()
        s = Scient(E, create_comp(earth=128))
        t = Scient(E, create_comp(earth=128))
        squad = Squad(name='xxx', data=[s, t])
        bf.rand_place_squad(squad)
        self.assertEqual(len(bf.find_units()), 2)
        self.assertEqual(bf.flush_units(), 2)
        self.assertEqual(len(bf.find_units()), 0)

    def test_dmg(self):
        bf = Battlefield()
        # attack with close combat weapon
        s = Scient(E, create_comp(earth=128))
        wep = Sword(E, create_comp(earth=128))
        s.equip(wep)
        t = Scient(F, create_comp(fire=128))
        bf.place_object(s, (0, 0))
        bf.place_object(t, (0, 1))
        self.assertEqual(bf.dmg(s, t), 1152)

        # attack with ranged weapon
        s.unequip()
        wep = Wand(E, create_comp(earth=128))
        s.equip(wep)
        self.assertEqual(bf.dmg(s, t), 1152)

        # attack with ranged weapon on same element enemy
        t = Scient(E, create_comp(earth=128))
        bf.place_object(t, (1, 0))
        self.assertEqual(bf.dmg(s, t), -640)

        # defender not on grid error
        t.location = Loc(-100, -100)
        self.assertRaises(ValueError, bf.dmg, s, t)

    def test_make_distance(self):
        bf = Battlefield()
        expect = {0: 5, 1: 7, 2: 7, 3: 5, 4: 7, 5: 7}
        self.assertEqual(bf.make_distances((0, 0), (4, 4)), expect)
        self.assertEqual(bf.make_distances((0, 1), (4, 3), direction=0), 3)
        self.assertEqual(bf.make_distances((0, 1), (4, 4), direction=0), 4)
        self.assertEqual(bf.make_distances((0, 0), (4, 3), direction=0), 4)

    def test_maxes(self):
        bf = Battlefield()
        expect = {0: 1, 1: 16, 2: 24, 3: 16, 4: 9, 5: 2}
        self.assertEqual(bf.maxes((0, 0)), expect)

    def test_calc_aoe(self):
        bf = Battlefield()
        s = Scient(E, create_comp(earth=128))
        bf.place_object(s, (0, 0))
        expect = [(1, 2), (2, 0), (1, 1)]
        self.assertEqual(sorted(bf.calc_AOE(s, (1, 1))), sorted(expect))
        self.assertEqual(bf.calc_AOE(s, (-1, -1)), set())

    def test_calc_ranged(self):
        # TODO -- when calc_ranged is implemented, update this
        self.assertIs(Battlefield().calc_ranged(None, None), None)

    def test_calc_damage(self):
        bf = Battlefield()
        # attack with Sword (short range)
        wep = Sword(E, create_comp(earth=128))
        s = Scient(E, create_comp(earth=128))
        s.equip(wep)
        t = Scient(F, create_comp(fire=128))
        bf.place_object(s, (0, 0))
        bf.place_object(t, (0, 1))
        self.assertEqual(bf.calc_damage(s, t), [(t, 1152)])

        # attack with Wand (AOE)
        s.unequip()
        wep = Wand(E, create_comp(earth=128))
        s.equip(wep)
        for i in xrange(1, 5):
            bf.place_object(t, (i, i))
        self.assertEqual(bf.calc_damage(s, t), [(t, 164)])

        # attack with Bow (ranged)
        s.unequip()
        wep = Bow(E, create_comp(earth=128))
        s.equip(wep)
        self.assertEqual(bf.calc_damage(s, t), [(t, 288)])

        # attack with Glove (DOT)
        s.unequip()
        wep = Glove(E, create_comp(earth=128))
        s.equip(wep)
        for i in reversed(range(1, 4)):
            bf.place_object(t, (i, i))
        bf.place_object(t, (0, 1))
        self.assertEqual(bf.calc_damage(s, t), [(t, 384)])

        # defender out of range raises exception
        for i in xrange(1, 16):
            bf.place_object(t, (i, i))
        self.assertRaises(ValueError, bf.calc_damage, s, t)

    def test_apply_damage(self):
        bf = Battlefield()
        bf.bury = MagicMock(side_effect=bf.bury)
        s = Scient(E, create_comp(earth=128))
        bf.place_object(s, (0, 0))
        s.hp = 101
        self.assertEqual(bf.apply_dmg(s, 100), 100)
        self.assertEqual(bf.apply_dmg(s, 100), 1)
        bf.bury.assert_called_once_with(s)

    def test_attack(self):
        bf = Battlefield()
        s = Scient(E, create_comp(earth=128))
        t = Nescient(F, create_comp(fire=128))
        wep = Glove(E, create_comp(earth=128))
        s.equip(wep)
        bf.place_object(s, (0, 0))
        bf.place_object(t, (1, 1))
        self.assertEqual(bf.attack(s, (1, 0)), [(t, 384)])
        self.assertRaises(ValueError, bf.attack, s, (5, 5))

    def test_get_dmg_queue(self):
        bf = Battlefield()
        self.assertEqual(bf.get_dmg_queue(), {})
        s = Scient(E, create_comp(earth=128))
        wep = Glove(E, create_comp(earth=128))
        s.equip(wep)
        t = Scient(F, create_comp(fire=128))
        bf.place_object(s, (0, 0))
        bf.place_object(t, (1, 0))
        bf.attack(s, (1, 0))
        self.assertEqual(bf.get_dmg_queue(), {t: [[384, 2]], s: []})
        return bf, s, t

    def test_apply_queued(self):
        bf, s, t = self.test_get_dmg_queue()
        self.assertEqual(bf.apply_queued(), [(t, 384)])
        self.assertEqual(bf.get_dmg_queue(), {t: [[384, 1]], s: []})
        self.assertEqual(bf.apply_queued(), [(t, 384)])
        self.assertEqual(bf.get_dmg_queue(), {t: [], s: []})
        self.assertEqual(bf.apply_queued(), [])
