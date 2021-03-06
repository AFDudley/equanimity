from unittest import TestCase
from equanimity.stone import Stone, Composition
from equanimity.const import ELEMENTS, E
from ..base import create_comp


class CompositionTest(TestCase):

    def assertValidComposition(self, c, val):
        for k, v in c.iteritems():
            self.assertIn(k, ELEMENTS)
            self.assertEqual(v, val)

    def test_create_no_value(self):
        c = Composition()
        self.assertValidComposition(c, -1)

    def test_create_value(self):
        c = Composition(111)
        self.assertValidComposition(c, 111)

    def test_create_bad_value(self):
        self.assertRaises(ValueError, Composition, -1)
        self.assertRaises(ValueError, Composition, 256)

    def test_create_from_keys(self):
        c = Composition.from_keys(earth=2, fire=2, ice=2, wind=2)
        self.assertValidComposition(c, 2)

    def test_create_from_keys_bad(self):
        self.assertRaises(ValueError, Composition.from_keys, earth=-100)

    def test_create_from_sequence(self):
        c = Composition.from_sequence((3, 3, 3, 3))
        self.assertValidComposition(c, 3)

    def test_create_from_sequence_bad(self):
        fs = Composition.from_sequence
        self.assertRaises(ValueError, fs, [])
        self.assertRaises(ValueError, fs, [1])
        self.assertRaises(ValueError, fs, [1, 2])
        self.assertRaises(ValueError, fs, [1, 2, 3])
        self.assertRaises(ValueError, fs, [1, 2, 3, 4, 5])
        self.assertRaises(ValueError, fs, [2, 3, 4, -10])
        self.assertRaises(ValueError, fs, [2, 3, 4, 256])

    def test_create_from_dict(self):
        c = Composition.from_dict({'Earth': 2, 'Ice': 2, 'Wind': 2, 'Fire': 2})
        self.assertValidComposition(c, 2)

    def test_create_from_dict_bad(self):
        self.assertRaises(ValueError, Composition.from_dict, {'Earth': 2})
        self.assertRaises(ValueError, Composition.from_dict, {'Earth': 2,
                                                              'Fire': 2})
        self.assertRaises(ValueError, Composition.from_dict, {'Earth': 2,
                                                              'Fire': 2,
                                                              'Wind': 2})
        self.assertRaises(ValueError, Composition.from_dict, {'Dog': 2})
        self.assertRaises(ValueError, Composition.from_dict, {'Earth': -100,
                                                              'Wind': 100,
                                                              'Fire': 100,
                                                              'Ice': 100})

    def test_create_wrapper(self):
        # Create with tuple
        c = Composition.create((4, 4, 4, 4))
        self.assertValidComposition(c, 4)
        # Create with list
        c = Composition.create([4, 4, 4, 4])
        self.assertValidComposition(c, 4)
        # Create with keyword args
        c = Composition.create(earth=4, ice=4, fire=4, wind=4)
        self.assertValidComposition(c, 4)
        # Create with dict
        c = Composition.create(dict(Earth=4, Ice=4, Wind=4, Fire=4))
        self.assertValidComposition(c, 4)
        # Create from positional args
        c = Composition.create(4, 4, 4, 4)
        self.assertValidComposition(c, 4)
        # Create from existing Composition (idempotent)
        d = Composition.create(c)
        self.assertValidComposition(d, 4)
        # It should make a new one as well
        self.assertNotEqual(id(c), id(d))


class StoneTest(TestCase):

    def test_create_stone(self):
        s = Stone()
        self.assertEqual(s.comp, create_comp())

    def test_create_with_limit(self):
        limit = create_comp(earth=128)
        s = Stone(limit=limit)
        self.assertEqual(s.limit, limit)

    def test_create_stone_with_stone(self):
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
        self.assertEqual(t.value, 128)
        self.assertEqual(s.value, 128 + 128 + 255)
        self.assertEqual(s.comp, create_comp(earth=128, ice=128, fire=255))
        self.assertEqual(t.comp, create_comp(fire=128))

    def test_imbue_stone_incomplete_comp(self):
        c = create_comp(ice=128)
        del c['Earth']
        self.assertRaises(ValueError, Stone, comp=c)

    def test_imbue_stone_destroying(self):
        s = Stone(create_comp(earth=64))
        t = Stone(create_comp(earth=32))
        self.assertIs(s.imbue(t), None)
        self.assertEqual(t.value, 0)

    def test_imbue_not_stone(self):
        s = Stone()
        self.assertRaises(TypeError, s.imbue, object())

    def test_tup(self):
        s = Stone(create_comp(earth=128, wind=64, ice=32, fire=16))
        self.assertEqual(s.tup(), (128, 16, 32, 64))

    def test_value(self):
        s = Stone(create_comp(earth=128, fire=32))
        self.assertEqual(s.value, 160)

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

    def test_repr(self):
        s = Stone([1, 2, 3, 4])
        self.assertEqual('<Stone: Earth: 1, Fire: 2, Ice: 3, Wind: 4>', str(s))

    def test_orth(self):
        s = Stone(Composition.create(earth=1, ice=3, fire=2, wind=4))
        self.assertEqual(s.orth(E), [2, 3])

    def test_opp(self):
        s = Stone(Composition.create(earth=1, ice=3, fire=2, wind=4))
        self.assertEqual(s.opp(E), 4)

    def test_extract_reward(self):
        s = Stone(create_comp(earth=7, ice=4))
        t = s.extract_award()
        self.assertEqual(t.comp, create_comp(earth=3, ice=2))
        self.assertEqual(s.comp, create_comp(earth=4, ice=2))

    def test_copy(self):
        s = Stone(create_comp(earth=128), limit=create_comp(earth=200))
        t = s.copy()
        self.assertNotEqual(id(s), id(t))
        self.assertEqual(s.comp, t.comp)
        self.assertEqual(s.limit, t.limit)
