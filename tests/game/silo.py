from unittest import TestCase
from equanimity.stone import Composition, Stone
from equanimity.silo import Silo


class SiloTest(TestCase):

    def test_create(self):
        s = Silo()
        self.assertEqual(s.limit, Composition(255))

    def test_create_with_limit(self):
        c = Composition(5)
        s = Silo(limit=c)
        self.assertEqual(s.limit, c)

    def test_create_with_comp(self):
        c = Composition(5)
        s = Silo(comp=c)
        self.assertEqual(s.comp, c)

    def test_get_simple(self):
        s = Silo()
        s.imbue(Composition(10))
        t = s.get(Composition(2))
        self.assertEqual(t.comp, Composition(2))
        self.assertEqual(s.comp, Composition(8))

    def test_get_transmute(self):
        s = Silo()
        start = Composition(10)
        s.imbue(start)
        c = Composition.create(1, 11, 1, 1)
        t = s.get(c)
        self.assertTrue(t)
        self.assertTrue(isinstance(t, Stone))

    def test_imbue_list(self):
        s = Silo()
        self.assertEqual(s.comp, Composition(0))
        nums = range(1, 10)
        comps = [Composition(x) for x in nums]
        s.imbue_list(comps)
        self.assertEqual(s.value(), sum(nums) * 4)
        for e in s:
            self.assertEqual(s[e], sum(nums))
