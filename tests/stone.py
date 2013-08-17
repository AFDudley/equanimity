from unittest import TestCase
from equanimity.stone import Stone
from base import create_comp

class StoneTest(TestCase):

    def test_create_stone(self):
        s = Stone()
        self.assertEqual(s.comp, create_comp())

    def test_create_stone_with_stone(self):
        stone = Stone()
        s = Stone(comp=Stone())
        self.assertEqual(s.comp, create_comp())

    def test_create_stone_with_dict(self):
        comp = create_comp(earth=128)
        s = Stone(comp=comp)
        self.assertEqual(s.comp, comp)

    def test_imbue_stone(self):
        s = Stone(create_comp(earth=128, fire=128))
        t = Stone(create_comp(ice=128, fire=255))
        self.assertEqual(t, s.imbue(t))
        self.assertEqual(t.value(), 128)
        self.assertEqual(s.value(), 256 + 255)
        self.assertEqual(s.comp, create_comp(earth=128, ice=128,
                                                   fire=255))
        self.assertEqual(t.comp, create_comp(fire=128))

    def test_imbue_stone_incomplete_comp(self):
        c = create_comp(ice=128)
        del c['Earth']
        self.assertRaises(ValueError, Stone, comp=c)

    def test_imbue_stone_destroying(self):
        s = Stone(create_comp(earth=64))
        t = Stone(create_comp(earth=32))
        self.assertIs(s.imbue(t), None)
        self.assertEqual(t.value(), 0)

    def test_imbue_not_stone(self):
        s = Stone()
        self.assertRaises(TypeError, s.imbue, object())

    def test_tup(self):
        s = Stone(create_comp(earth=128, wind=64, ice=32, fire=16))
        self.assertEqual(s.tup(), (128, 16, 32, 64))

    def test_value(self):
        s = Stone(create_comp(earth=128, fire=32))
        self.assertEqual(s.value(), 160)

    def test_split(self):
        s = Stone(create_comp(earth=128))
        c = create_comp(earth=32)
        t = s.split(c)
        self.assertEqual(t.comp, create_comp(earth=32))
        self.assertEqual(s.comp, create_comp(earth=96))

    def test_split_bad(self):
        s = Stone(create_comp(earth=128))
        c = create_comp(earth=255)
        self.assertRaises(ValueError, s.split, c)
        s = Stone(create_comp(earth=128, fire=255))
        c = create_comp(earth=196)
        self.assertRaises(ValueError, s.split, c)

    def test_contains(self):
        s = Stone(create_comp(earth=255))
        self.assertIn('Earth', s)

    def test_getitem(self):
        s = Stone(create_comp(earth=255))
        self.assertEqual(s['Earth'], 255)

    def test_setitem(self):
        s = Stone(create_comp(earth=255))
        s['Earth'] = 10
        self.assertEqual(s['Earth'], 10)

    def test_setitem_bad(self):
        s = Stone(create_comp(earth=255))
        s.limit['Ice'] = 10
        self.assertRaises(AttributeError, s.__setitem__, 'Ice', 20)

    def test_len(self):
        s = Stone(create_comp())
        self.assertEqual(len(s), 4)

    def test_hash(self):
        s = Stone()
        self.assertEqual(hash(s), id(s))
