from unittest import TestCase
from equanimity.const import E
from equanimity.weapons import Sword, Bow, Glove, Wand, Weapon
from ..base import create_comp


class WeaponTest(TestCase):

    def setUp(self):
        super(WeaponTest, self).setUp()
        self.w = Weapon(E, create_comp(earth=128), 'Gun')

    def test_map_to_grid(self):
        origin = (4, 4)
        grid_size = (8, 8)
        grid = self.w.map_to_grid(origin, grid_size)
        expected = [(4, 3), (5, 4), (4, 5), (3, 4), (3, 3), (3, 5), (5, 5),
                    (5, 3)]
        self.assertEqual(grid, expected)

    def test_make_pattern(self):
        origin = (4, 4)
        distance = 2
        pointing = ['North', 'South', 'East', 'West']
        expected = dict(North=[(4, 3), (3, 2), (4, 2), (5, 2)],
                        South=[(4, 5), (3, 6), (4, 6), (5, 6)],
                        East=[(5, 4), (6, 5), (6, 4), (6, 3)],
                        West=[(3, 4), (2, 5), (2, 4), (2, 3)])
        for direction in pointing:
            p = self.w.make_pattern(origin, distance, direction)
            print direction, p
            self.assertEqual(p, expected[direction])

    def test_attack_pattern(self):
        p = [(0, -1), (1, 0), (0, 1), (-1, 0), (-1, -1), (-1, 1), (1, 1),
             (1, -1)]
        self.assertEqual(self.w.get_attack_pattern(), p)


class SwordTest(TestCase):

    def test_sword(self):
        comp = create_comp(earth=128)
        s = Sword(E, comp)
        self.assertEqual(s.comp, comp)
        self.assertEqual(s.type, 'Sword')


class BowTest(TestCase):

    def setUp(self):
        super(BowTest, self).setUp()
        self.comp = create_comp(earth=128)
        self.w = Bow(E, self.comp)

    def test_bow(self):
        self.assertEqual(self.w.comp, self.comp)
        self.assertEqual(self.w.type, 'Bow')

    def test_get_attack_pattern(self):
        grid = self.w.get_attack_pattern()
        expected = [(-8, 0), (-7, -1), (-7, 0), (-7, 1), (-6, -2), (-6, -1),
                    (-6, 0), (-6, 1), (-6, 2), (-5, -3), (-5, -2), (-5, -1),
                    (-5, 0), (-5, 1), (-5, 2), (-5, 3), (-4, -4), (-4, -3),
                    (-4, -2), (-4, -1), (-4, 1), (-4, 2), (-4, 3), (-4, 4),
                    (-3, -5), (-3, -4), (-3, -3), (-3, -2), (-3, 2), (-3, 3),
                    (-3, 4), (-3, 5), (-2, -6), (-2, -5), (-2, -4), (-2, -3),
                    (-2, 3), (-2, 4), (-2, 5), (-2, 6), (-1, -7), (-1, -6),
                    (-1, -5), (-1, -4), (-1, 4), (-1, 5), (-1, 6), (-1, 7),
                    (0, -8), (0, -7), (0, -6), (0, -5), (0, 5), (0, 6), (0, 7),
                    (0, 8), (1, -7), (1, -6), (1, -5), (1, -4), (1, 4), (1, 5),
                    (1, 6), (1, 7), (2, -6), (2, -5), (2, -4), (2, -3), (2, 3),
                    (2, 4), (2, 5), (2, 6), (3, -5), (3, -4), (3, -3), (3, -2),
                    (3, 2), (3, 3), (3, 4), (3, 5), (4, -4), (4, -3), (4, -2),
                    (4, -1), (4, 1), (4, 2), (4, 3), (4, 4), (5, -3), (5, -2),
                    (5, -1), (5, 0), (5, 1), (5, 2), (5, 3), (6, -2), (6, -1),
                    (6, 0), (6, 1), (6, 2), (7, -1), (7, 0), (7, 1), (8, 0)]
        self.assertEqual(grid, expected)


class GloveTest(TestCase):

    def test_glove(self):
        comp = create_comp(earth=128)
        s = Glove(E, comp)
        self.assertEqual(s.comp, comp)
        self.assertEqual(s.type, 'Glove')
        self.assertEqual(s.time, 3)


class WandTest(TestCase):

    def setUp(self):
        super(WandTest, self).setUp()
        self.comp = create_comp(earth=128)
        self.w = Wand(E, self.comp)

    def test_wand(self):
        self.assertEqual(self.w.comp, self.comp)
        self.assertEqual(self.w.type, 'Wand')

    def test_wand_map_to_grid(self):
        origin = (4, 4)
        grid_size = (8, 8)
        grid = self.w.map_to_grid(origin, grid_size)
        expected = [
            (3, 4), (2, 5), (2, 4), (2, 3), (1, 6), (1, 5), (1, 4), (1, 3),
            (1, 2), (0, 7), (0, 6), (0, 5), (0, 4), (0, 3), (0, 2), (0, 1),
            (4, 3), (3, 2), (4, 2), (5, 2), (2, 1), (3, 1), (4, 1), (5, 1),
            (6, 1), (1, 0), (2, 0), (3, 0), (4, 0), (5, 0), (6, 0), (7, 0),
            (5, 4), (6, 5), (6, 4), (6, 3), (7, 6), (7, 5), (7, 4), (7, 3),
            (7, 2), (4, 5), (3, 6), (4, 6), (5, 6), (2, 7), (3, 7), (4, 7),
            (5, 7), (6, 7)]
        self.assertEqual(grid, expected)

    def test_wand_make_pattern(self):
        origin = (4, 4)
        distance = 2
        pointing = 'North'
        p = self.w.make_pattern(origin, distance, pointing)
        self.assertEqual(p, [(4, 3), (3, 2), (4, 2), (5, 2)])

    def test_wand_get_attack_pattern(self):
        self.assertRaises(UserWarning, self.w.get_attack_pattern)
