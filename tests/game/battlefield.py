from mock import MagicMock
from equanimity.grid import Grid, Hex
from equanimity.units import Scient, Nescient
from equanimity.unit_container import Squad
from equanimity.battlefield import Battlefield
from equanimity.field import Field
from equanimity.stone import Stone
from equanimity.const import E, F, I
from equanimity.weapons import Sword, Wand, Bow, Glove
from ..base import create_comp, FlaskTestDBWorld


class BattlefieldTest(FlaskTestDBWorld):

    def create_battlefield(self, field=None, defsquad=None, atksquad=None):
        if field is None:
            field = Field(self.world, Hex(0, 0), I)
        if defsquad is None:
            s = Scient(E, create_comp(earth=128))
            defsquad = Squad(data=[s])
        if atksquad is None:
            s = Scient(E, create_comp(earth=128))
            atksquad = Squad(data=[s])
        return Battlefield(field, defsquad, atksquad)

    def test_create(self):
        s = Scient(E, create_comp(earth=128))
        defsquad = Squad(data=[s])
        t = Scient(E, create_comp(earth=128))
        atksquad = Squad(data=[t])
        field = Field(self.world, Hex(0, 0), I)
        bf = self.create_battlefield(field=field, defsquad=defsquad,
                                     atksquad=atksquad)
        self.assertEqual(bf.grid, field.grid)
        self.assertEqual(bf.field, field)
        self.assertEqual(bf.graveyard, [])
        self.assertEqual(bf.defsquad, defsquad)
        self.assertEqual(bf.atksquad, atksquad)
        self.assertEqual(bf.dmg_queue, {})
        self.assertEqual(bf.squads, (defsquad, atksquad))
        self.assertEqual(bf.units, (s, t))
        self.assertEqual(len(bf.ranged), 5)
        self.assertEqual(len(bf.DOT), 5)
        self.assertEqual(len(bf.AOE), 5)
        self.assertEqual(len(bf.Full), 5)

    def test_create_with_defsquad(self):
        d = Squad()
        bf = self.create_battlefield(defsquad=d)
        self.assertEqual(bf.defsquad, d)

    def test_create_with_atksquad(self):
        a = Squad()
        bf = self.create_battlefield(atksquad=a)
        self.assertEqual(bf.atksquad, a)

    def test_get_units(self):
        dss = Scient(E, (20, 0, 0, 0))
        ass = Scient(F, (0, 20, 0, 0))
        dsq = Squad(name='def', data=[dss])
        asq = Squad(name='atk', data=[ass])
        bf = self.create_battlefield(atksquad=asq, defsquad=dsq)
        self.assertEqual(bf.get_units(), (dss, ass))

    def test_on_grid(self):
        grid = Grid(radius=4)
        field = Field(self.world, Hex(0, 0), I, grid=grid)
        bf = self.create_battlefield(field=field)
        self.assertTrue(bf.grid.in_bounds((1, 3)))
        self.assertFalse(bf.grid.in_bounds((2, 10)))

    def test_make_parts(self):
        bf = self.create_battlefield()
        body = bf.make_parts(dict(x='east', y='west'))
        for part in body.itervalues():
            self.assertIn(part.location, ['east', 'west'])

    def test_make_body(self):
        bf = self.create_battlefield()
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
        bf = self.create_battlefield()
        body = bf.make_body((4, 4), 'North')
        self.assertTrue(bf.body_on_grid(body))
        for p in body.itervalues():
            p.location = map(lambda x: x - 200, p.location)
        self.assertFalse(bf.body_on_grid(body))

    def test_can_move_nescient(self):
        bf = self.create_battlefield()
        body = bf.make_body((4, 4), 'North')
        nes = Nescient(E, create_comp(earth=128))
        self.assertTrue(bf.can_move_nescient(body, nes))
        x, y = body.values()[0].location
        bf.grid[x][y].contents = Scient(E, create_comp(earth=128))
        self.assertFalse(bf.can_move_nescient(body, nes))

    def test_move_nescient(self):
        bf = self.create_battlefield()
        nes = Nescient(E, create_comp(earth=128))
        nes.take_body = MagicMock(side_effect=nes.take_body)
        body = bf.make_body((4, 4), 'North')
        self.assertTrue(bf.move_nescient(body, nes))
        nes.take_body.assert_called_with(body)
        self.assertEqual(nes.location, body['right'].location)

        # blocked movement
        del nes.__dict__['take_body']  # get rid of the mock to shut up pickle
        x, y = body.values()[0].location
        bf.grid[x][y].contents = Scient(E, create_comp(earth=128))
        self.assertRaises(ValueError, bf.move_nescient, body, nes)

    def test_place_nescient(self):
        bf = self.create_battlefield()
        nes = Nescient(E, create_comp(earth=128))
        # Bad dest error
        nes.chosen_location = (-100, -100)
        self.assertRaises(ValueError, bf.place_nescient, nes)

        # Body not on grid error
        nes.chosen_location = (-bf.grid.radius, bf.grid.radius)
        nes.facing = 'South'
        self.assertRaises(ValueError, bf.place_nescient, nes)

        # Null placement
        nes.chosen_location = Hex.null
        self.assertRaises(ValueError, bf.place_nescient, nes)

        # Valid placement
        nes.chosen_location = (2, 2)
        self.assertTrue(bf.place_nescient(nes))

        # Replacement
        self.assertRaises(ValueError, bf.place_nescient, nes)

    def test_get_rotations(self):
        # Test unable to move at all
        g = Grid(radius=1)
        f = Field(self.world, Hex(0, 0), I, grid=g)
        bf = self.create_battlefield(field=f)
        nes = Nescient(E, create_comp(earth=128))
        nes.body = bf.make_body((-16, 16), 'North')
        self.assertFalse(bf.get_rotations(nes))

        f = Field(self.world, Hex(0, 0), I, grid=Grid(radius=16))
        bf = self.create_battlefield(f)
        nes = Nescient(E, create_comp(earth=128))
        nes.body = bf.make_body((4, 4), 'North')
        dirs = sorted(bf.grid.directions.values())
        self.assertEqual(sorted(bf.get_rotations(nes)), dirs)

    def test_rotate(self):
        bf = self.create_battlefield()
        nes = Nescient(E, create_comp(earth=128))
        nes.body = bf.make_body((4, 4), 'North')
        self.assertTrue(bf.rotate(nes, 'Northeast'))
        self.assertEqual(nes.facing, 'Northeast')

        nes.body = bf.make_body((-16, 16), 'North')
        self.assertRaises(ValueError, bf.rotate, nes, 'South')

    def test_map_to_grid(self):
        f = Field(self.world, Hex(0, 0), I, grid=Grid(radius=16))
        bf = self.create_battlefield(field=f)
        expect = [
            (-4, 4), (-4, 5), (-4, 6), (-4, 7), (-4, 8), (-4, 9), (-4, 10),
            (-4, 11), (-4, 12), (-3, 3), (-3, 4), (-3, 5), (-3, 6), (-3, 7),
            (-3, 8), (-3, 9), (-3, 10), (-3, 11), (-3, 12), (-2, 2), (-2, 3),
            (-2, 4), (-2, 5), (-2, 6), (-2, 7), (-2, 8), (-2, 9), (-2, 10),
            (-2, 11), (-2, 12), (-1, 1), (-1, 2), (-1, 3), (-1, 4), (-1, 5),
            (-1, 6), (-1, 7), (-1, 8), (-1, 9), (-1, 10), (-1, 11), (-1, 12),
            (0, 0), (0, 1), (0, 2), (0, 3), (0, 9), (0, 10), (0, 11), (0, 12),
            (1, -1), (1, 0), (1, 1), (1, 2), (1, 9), (1, 10), (1, 11), (1, 12),
            (2, -2), (2, -1), (2, 0), (2, 1), (2, 9), (2, 10), (2, 11),
            (2, 12), (3, -3), (3, -2), (3, -1), (3, 0), (3, 9), (3, 10),
            (3, 11), (3, 12), (4, -4), (4, -3), (4, -2), (4, -1), (4, 9),
            (4, 10), (4, 11), (4, 12), (5, -4), (5, -3), (5, -2), (5, -1),
            (5, 8), (5, 9), (5, 10), (5, 11), (6, -4), (6, -3), (6, -2),
            (6, -1), (6, 7), (6, 8), (6, 9), (6, 10), (7, -4), (7, -3),
            (7, -2), (7, -1), (7, 6), (7, 7), (7, 8), (7, 9), (8, -4), (8, -3),
            (8, -2), (8, -1), (8, 5), (8, 6), (8, 7), (8, 8), (9, -4), (9, -3),
            (9, -2), (9, -1), (9, 0), (9, 1), (9, 2), (9, 3), (9, 4), (9, 5),
            (9, 6), (9, 7), (10, -4), (10, -3), (10, -2), (10, -1), (10, 0),
            (10, 1), (10, 2), (10, 3), (10, 4), (10, 5), (10, 6), (11, -4),
            (11, -3), (11, -2), (11, -1), (11, 0), (11, 1), (11, 2), (11, 3),
            (11, 4), (11, 5), (12, -4), (12, -3), (12, -2), (12, -1), (12, 0),
            (12, 1), (12, 2), (12, 3), (12, 4)
        ]
        got = bf.map_to_grid((4, 4), Wand(E, create_comp(earth=128)))
        self.assertEqual(sorted(list(expect)), sorted(list(map(tuple, got))))
        expect = [(3, 4), (3, 5), (4, 3), (4, 5), (5, 3), (5, 4)]
        got = bf.map_to_grid((4, 4), Sword(E, create_comp(earth=128)))
        self.assertEqual(sorted(list(expect)), sorted(list(map(tuple, got))))

    def test_place_object(self):
        bf = self.create_battlefield()
        # bad obj
        self.assertRaises(TypeError, bf.place_object, None)
        # scient placement
        s = Scient(E, create_comp(earth=128))
        s.chosen_location = Hex(0, 1)
        self.assertTrue(bf.place_object(s))
        # nescient placement
        nes = Nescient(E, create_comp(earth=128))
        nes.chosen_location = Hex(4, 4)
        self.assertTrue(bf.place_object(nes))
        # stone placement
        s = Stone(create_comp(earth=128))
        self.assertRaises(NotImplementedError, bf.place_object, s)

    def test_move_scient(self):
        bf = self.create_battlefield()
        # same spot
        self.assertFalse(bf.move_scient((0, 0), (0, 0)))
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
        self.assertEqual(s.location, Hex(1, 1))

    def test_place_scient(self):
        bf = self.create_battlefield()
        s = Scient(E, create_comp(earth=128))
        # placing off grid
        s.chosen_location = Hex(-100, -100)
        self.assertRaises(ValueError, bf.place_scient, s)
        # valid placement
        s.chosen_location = Hex(0, 0)
        self.assertTrue(bf.place_scient(s))
        self.assertEqual(bf.grid[0][0].contents, s)
        self.assertEqual(s.location, Hex(0, 0))
        self.assertEqual(bf.dmg_queue[s], [])
        # replacement
        self.assertRaises(ValueError, bf.place_scient, s)
        # null dest
        s = Scient(E, create_comp(earth=128))
        s.chosen_location = Hex.null
        self.assertRaises(ValueError, bf.place_scient, s)
        # placing in occupied spot
        t = Scient(E, create_comp(earth=128))
        t.chosen_location = Hex(0, 0)
        self.assertRaises(ValueError, bf.place_scient, t)

    def test_find_units(self):
        s = Scient(E, create_comp(earth=128))
        s.chosen_location = Hex(0, 0)
        bf = self.create_battlefield()
        bf.place_object(s)
        s = Scient(E, create_comp(earth=128))
        s.chosen_location = Hex(2, 2)
        bf.place_object(s)
        self.assertEqual(list(bf.grid.occupied_coords()), [(0, 0), (2, 2)])

    def test_flush_units(self):
        s = Scient(E, create_comp(earth=128))
        t = Scient(E, create_comp(earth=128))
        s.chosen_location = Hex(0, 0)
        t.chosen_location = Hex(0, 1)
        squad = Squad(name='xxx', data=[s, t])
        u = Scient(E, create_comp(earth=128))
        u.chosen_location = Hex(2, 1)
        atksquad = Squad(data=[u])
        bf = self.create_battlefield(defsquad=squad, atksquad=atksquad)
        bf.field.rand_place_squad(squad)
        bf.put_squads_on_field()
        self.assertEqual(len(list(bf.grid.occupied_coords())), 3)
        self.assertEqual(bf.flush_units(), 3)
        self.assertEqual(len(list(bf.grid.occupied_coords())), 0)

    def test_dmg(self):
        bf = self.create_battlefield()
        # attack with close combat weapon
        s = Scient(E, create_comp(earth=128))
        wep = Sword(E, create_comp(earth=128))
        s.equip(wep)
        s.chosen_location = Hex(0, 0)
        t = Scient(F, create_comp(fire=128))
        t.chosen_location = Hex(0, 1)
        bf.place_object(s)
        bf.place_object(t)
        self.assertEqual(bf.dmg(s, t), 1152)

        # attack with ranged weapon
        s.unequip()
        wep = Wand(E, create_comp(earth=128))
        s.equip(wep)
        self.assertEqual(bf.dmg(s, t), 1152)

        # attack with ranged weapon on same element enemy
        t = Scient(E, create_comp(earth=128))
        t.chosen_location = Hex(1, 0)
        bf.place_object(t)
        self.assertEqual(bf.dmg(s, t), -640)

        # defender not on grid error
        t.location = Hex(-100, -100)
        self.assertRaises(ValueError, bf.dmg, s, t)

    def test_calc_aoe(self):
        bf = self.create_battlefield()
        s = Scient(E, create_comp(earth=128))
        s.chosen_location = Hex(0, 0)
        bf.place_object(s)
        expect = sorted([(2, -2), (2, -1), (2, 0)])
        self.assertEqual(sorted(bf.calc_aoe(s, (2, -2))), expect)
        self.assertEqual(sorted(bf.calc_aoe(s, (2, -1))), expect)
        self.assertEqual(bf.calc_aoe(s, (-100, -100)), set())

    def test_calc_ranged(self):
        # TODO -- when calc_ranged is implemented, update this
        self.assertIs(self.create_battlefield().calc_ranged(None, None), None)

    def test_calc_damage(self):
        f = Field(self.world, Hex(0, 0), I, grid=Grid(radius=16))
        bf = self.create_battlefield(field=f)
        # attack with Sword (short range)
        wep = Sword(E, create_comp(earth=128))
        s = Scient(E, create_comp(earth=128))
        s.equip(wep)
        t = Scient(F, create_comp(fire=128))
        s.chosen_location = Hex(0, 0)
        t.chosen_location = Hex(0, 1)
        bf.place_object(s)
        bf.place_object(t)
        self.assertEqual(bf.calc_damage(s, t), [[t, 1152]])

        # attack with Wand (AOE)
        s.unequip()
        wep = Wand(E, create_comp(earth=128))
        s.equip(wep)
        for i in xrange(1, 4):
            bf.move_scient(t.location, (i, i))
        self.assertEqual(bf.calc_damage(s, t), [[t, 164]])

        # attack with Bow (ranged)
        s.unequip()
        wep = Bow(E, create_comp(earth=128))
        s.equip(wep)
        self.assertEqual(bf.calc_damage(s, t), [[t, 288]])

        # attack with Glove (DOT)
        s.unequip()
        wep = Glove(E, create_comp(earth=128))
        s.equip(wep)
        for i in reversed(range(1, 4)):
            bf.move_scient(t.location, (i, i))
        bf.move_scient(t.location, (0, 1))
        self.assertEqual(bf.calc_damage(s, t), [[t, 384]])

        # defender out of range raises exception
        for i in xrange(1, 8):
            bf.move_scient(t.location, (i, i))
        self.assertRaises(ValueError, bf.calc_damage, s, t)

    def test_apply_damage(self):
        bf = self.create_battlefield()
        bf.bury = MagicMock(side_effect=bf.bury)
        s = Scient(E, create_comp(earth=128))
        s.chosen_location = Hex(0, 0)
        bf.place_object(s)
        s.hp = 101
        self.assertEqual(bf.apply_dmg(s, 100), 100)
        self.assertEqual(bf.apply_dmg(s, 100), 1)
        bf.bury.assert_called_once_with(s)

    def test_attack(self):
        f = Field(self.world, Hex(0, 0), I, grid=Grid(radius=16))
        bf = self.create_battlefield(field=f)
        s = Scient(E, create_comp(earth=128))
        t = Nescient(F, create_comp(fire=128))
        wep = Glove(E, create_comp(earth=128))
        s.equip(wep)
        s.chosen_location = Hex(0, 0)
        t.chosen_location = Hex(1, 1)
        bf.place_object(s)
        bf.place_object(t)
        self.assertEqual(bf.attack(s, (1, 0)), [[t, 384]])
        self.assertRaises(ValueError, bf.attack, s, (5, 5))
        try:
            bf.attack(s, (5, 5))
        except ValueError as e:
            self.assertIn('Nothing to attack', str(e))
        else:
            self.fail('ValueError not raised')

    def test_get_dmg_queue(self):
        bf = self.create_battlefield()
        self.assertEqual(bf.get_dmg_queue(), {})
        s = Scient(E, create_comp(earth=128))
        wep = Glove(E, create_comp(earth=128))
        s.equip(wep)
        t = Scient(F, create_comp(fire=128))
        s.chosen_location = Hex(0, 0)
        t.chosen_location = Hex(1, 0)
        bf.place_object(s)
        bf.place_object(t)
        bf.attack(s, (1, 0))
        self.assertEqual(bf.get_dmg_queue(), {t: [[384, 2]], s: []})
        return bf, s, t

    def test_apply_queued(self):
        bf, s, t = self.test_get_dmg_queue()
        self.assertEqual(bf.apply_queued(), [[t, 384]])
        self.assertEqual(bf.get_dmg_queue(), {t: [[384, 1]], s: []})
        self.assertEqual(bf.apply_queued(), [[t, 384]])
        self.assertEqual(bf.get_dmg_queue(), {t: [], s: []})
        self.assertEqual(bf.apply_queued(), [])
