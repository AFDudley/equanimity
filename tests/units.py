from unittest import TestCase
from equanimity.units import Unit, Scient, Nescient, Part
from equanimity.const import E
from base import create_comp


class UnitsTest(TestCase):

    def setUp(self):
        super(UnitsTest, self).setUp()
        self.comp = create_comp(earth=128)
        self.u = Unit(E, self.comp, name='x')

    def test_create(self):
        self.assertEqual(self.u.name, 'x')
        self.assertEqual(self.u.comp, self.comp)

    def test_create_unknown_element(self):
        self.assertRaises(Exception, Unit, 'adadasd', create_comp())

    def test_create_bad_primary_element(self):
        self.assertRaises(ValueError, Unit, E, create_comp(earth=0))

    def test_create_bad_opposite_element(self):
        self.assertRaises(ValueError, Unit, E, create_comp(earth=128, wind=1))

    def test_calcstats(self):
        pass

    def test_stats(self):
        pass

    def test_repr(self):
        self.assertEqual(self.u.name, str(self.u))


class ScientTest(TestCase):

    def test_create(self):
        pass

    def test_imbue(self):
        pass

    def test_equip(self):
        pass

    def test_unequip(self):
        pass


class Nescient(TestCase):

    def test_create(self):
        pass

    def test_take_body(self):
        pass

    def test_calcstats(self):
        pass


class PartTest(TestCase):

    def test_create(self):
        pass

    def test_hp(self):
        pass
