from random import randint
from unittest import TestCase
from equanimity.units import Unit, Scient, Nescient, Part
from equanimity.weapons import Glove
from equanimity.const import E, I, W, F, ELEMENTS, ORTH
from equanimity.stone import Stone
from base import create_comp


class UnitsTest(TestCase):

    def setUp(self):
        super(UnitsTest, self).setUp()
        self.comp = create_comp(earth=128)
        self.u = Unit(E, self.comp, name='x')

    def test_create(self):
        self.assertEqual(self.u.name, 'x')
        self.assertEqual(self.u.comp, self.comp)

    def test_create_no_name(self):
        self.u = Unit(E, self.comp)
        self.assertIsNot(self.u.name, None)
        self.assertTrue(isinstance(self.u.name, basestring))

    def test_create_sex(self):
        u = Unit(E, self.comp, sex='male')
        self.assertEqual(u.sex, 'male')

    def test_create_unknown_element(self):
        self.assertRaises(Exception, Unit, 'adadasd', create_comp())

    def test_create_bad_primary_element(self):
        self.assertRaises(ValueError, Unit, E, create_comp(earth=0))

    def test_create_bad_opposite_element(self):
        self.assertRaises(ValueError, Unit, E, create_comp(earth=128, wind=1))

    def test_calcstats(self):
        expect = {'mdef': 384, 'pdef': 768, 'hp': 5120, 'm': 128, 'atk': 384,
                  'p': 256, 'defe': 256, 'patk': 640, 'matk': 512}
        self.u.calcstats()
        self.assertEqual(expect, self.u.stats())

    def test_stats(self):
        expect = {}
        for s in self.u.attrs:
            val = randint(0, 10000)
            expect[s] = val
            setattr(self.u, s, val)
        self.assertEqual(expect, self.u.stats())

    def test_repr(self):
        self.assertEqual(self.u.name, str(self.u))


class ScientTest(TestCase):

    def setUp(self):
        super(ScientTest, self).setUp()
        self.comp = create_comp(earth=128)
        self.s = Scient(E, self.comp)

    def test_create(self):
        self.assertEqual(self.s.move, 4)
        self.assertIs(self.s.weapon, None)
        expect = {'mdef': 384, 'pdef': 768, 'hp': 5120, 'm': 128, 'atk': 384,
                  'p': 256, 'defe': 256, 'patk': 640, 'matk': 512}
        self.assertEqual(expect, self.s.stats())

    def test_create_weapon(self):
        wep = Glove(E, self.comp)
        self.s = Scient(E, self.comp, weapon=wep)
        self.assertEqual(self.s.weapon, wep)

    def test_create_sex(self):
        self.s = Scient(E, self.comp, sex='male')
        self.assertEqual(self.s.sex, 'male')

    def test_create_weapon_bonus(self):
        bonus = Stone(create_comp(earth=64))
        self.s = Scient(E, self.comp, weapon_bonus=bonus)
        self.assertEqual(self.s.weapon_bonus, bonus)

    def test_create_weapon_bonus_too_much(self):
        bonus = Stone(create_comp(earth=128))
        self.assertRaises(AttributeError, Scient, E, self.comp,
                          weapon_bonus=bonus)

    def test_create_bad_elements(self):
        comp = create_comp(earth=1, ice=20, fire=20, wind=20)
        self.assertRaises(ValueError, Scient, E, comp)

    def test_imbue(self):
        s = Scient(E, create_comp(earth=128, fire=32))
        t = Stone(create_comp(ice=32, fire=32))
        self.assertIs(s.imbue(t), None)
        self.assertEqual(t.value(), 0)
        self.assertEqual(s.value(), 128 + 32 + 32 + 32)
        self.assertEqual(s.comp, create_comp(earth=128, ice=32, fire=64))
        self.assertEqual(t.comp, create_comp())

    def test_imbue_bad_primary_element(self):
        stone = Stone(create_comp(wind=128))
        self.assertRaises(Exception, self.s.imbue, stone)

    def test_imbue_bad_orthogonal_element(self):
        stone = Stone(create_comp(ice=200, fire=200))
        self.assertRaises(ValueError, self.s.imbue, stone)

    def test_equip(self):
        self.assertIs(self.s.weapon, None)
        wep = Glove(E, self.comp)
        self.s.equip(wep)
        self.assertEqual(self.s.weapon, wep)

    def test_unequip(self):
        self.assertIs(self.s.weapon, None)
        wep = Glove(E, self.comp)
        self.s.equip(wep)
        self.assertEqual(self.s.weapon, wep)
        rem_wep = self.s.unequip()
        self.assertIs(self.s.weapon, None)
        self.assertEqual(rem_wep, wep)


class NescientTest(TestCase):

    def setUp(self):
        super(NescientTest, self).setUp()
        self.nes = Nescient(E, create_comp(earth=128))

    def test_create(self):
        self.assertEqual(self.nes.sex, 'female')
        for p in self.nes.body.itervalues():
            self.assertIsNot(p, None)

        for el in ELEMENTS:
            comp = create_comp()
            comp[el] = 128
            n = Nescient(el, comp)
            # Test for AOE comps
            if el == I:
                self.assertEqual(n.kind, 'm')
                self.assertEqual(n.type, 'Icestorm')
            elif el == W:
                self.assertEqual(n.kind, 'm')
                self.assertEqual(n.type, 'Blizzard')
            elif el == F:
                self.assertEqual(n.kind, 'p')
                self.assertEqual(n.type, 'Firestorm')
            elif el == E:
                self.assertEqual(n.kind, 'p')
                self.assertEqual(n.type, 'Avalanche')
            else:
                self.assertTrue(False)

            # Test for ranged comps
            comp[ORTH[el][0]] = 32
            n = Nescient(el, comp)
            if el == I:
                self.assertEqual(n.kind, 'm')
                self.assertEqual(n.type, 'Permafrost')
            elif el == W:
                self.assertEqual(n.kind, 'm')
                self.assertEqual(n.type, 'Pyrocumulus')
            elif el == F:
                self.assertEqual(n.kind, 'p')
                self.assertEqual(n.type, 'Forestfire')
            elif el == E:
                self.assertEqual(n.kind, 'p')
                self.assertEqual(n.type, 'Magma')
            else:
                self.assertTrue(False)

    def test_create_bad(self):
        # both orthogonals > 0
        self.assertRaises(ValueError, Nescient, E,
                          create_comp(earth=100, fire=50, ice=50))
        # orthogonals exceeding primary element
        self.assertRaises(ValueError, Nescient, E,
                          create_comp(earth=100, fire=150))

    def test_take_body(self):
        nes = Nescient(I, create_comp(ice=128))
        body = nes.body
        for p in body.itervalues():
            self.assertEqual(p.nescient, nes)
        self.nes.take_body(body)
        for p in body.itervalues():
            self.assertEqual(p.nescient, self.nes)
        self.assertEqual(self.nes.body, body)

    def test_calcstats(self):
        expect = {'mdef': 384, 'pdef': 768, 'hp': 20480, 'm': 128, 'atk': 640,
                  'p': 256, 'defe': 256, 'patk': 640, 'matk': 512}
        print self.nes.stats()
        self.nes.calcstats()
        self.assertEqual(expect, self.nes.stats())


class PartTest(TestCase):

    def setUp(self):
        super(PartTest, self).setUp()
        self.nes = Nescient(E, create_comp(earth=128))
        self.nes.hp = 70

    def test_create(self):
        p = Part(self.nes, location='x')
        self.assertEqual(p.nescient, self.nes)
        self.assertEqual(p.location, 'x')

    def test_hp(self):
        p = Part(self.nes)
        self.assertEqual(p.hp, self.nes.hp)
        p.hp = 202
        self.assertEqual(self.nes.hp, 202)
