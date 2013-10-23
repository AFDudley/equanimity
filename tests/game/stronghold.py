from voluptuous import Schema
from equanimity.grid import Hex
from equanimity.const import E
from equanimity.stronghold import Stronghold, MappedContainer, SparseList
from server.utils import AttributeDict
from ..base import FlaskTestDB, FlaskTestDBWorld, create_comp


class MappedContainerTest(FlaskTestDB):

    def setUp(self):
        super(MappedContainerTest, self).setUp()
        self.m = MappedContainer()

    def _make_value(self, uid):

        class AttributeDictUID(AttributeDict):

            def __eq__(self, other):
                return self.uid == other.uid

            def __ne__(self, other):
                return not self.__eq__(other)

        return AttributeDictUID(uid=uid, size=1, value=lambda: 5,
                                remove_from_container=lambda: True,
                                add_to_container=lambda x, y: True)

    def test_create(self):
        self.assertEqual(self.m.name, 'stronghold')
        self.assertTrue(hasattr(self.m, 'map'))

    def test_setitem_getitem_delitem(self):
        val = self._make_value(2)
        self.m[2] = val
        self.assertEqual(self.m[2], val)
        del self.m[2]
        self.assertRaises(KeyError, self.m.__getitem__, 2)

    def test_setitem_bad(self):
        self.assertRaises(KeyError, self.m.__setitem__, 2, self._make_value(3))

    def test_contains(self):
        val = self._make_value(7)
        self.m[7] = val
        self.assertIn(7, self.m)

    def test_append(self):
        val = self._make_value(7)
        self.m.append(val)
        self.assertIn(7, self.m)
        # reappend overwrites
        valx = self._make_value(7)
        self.m.append(valx)
        self.assertNotEqual(id(val), id(valx))
        self.assertEqual(id(self.m[7]), id(valx))

    def test_pop(self):
        val = self._make_value(7)
        self.m[7] = val
        r = self.m.pop(7)
        self.assertEqual(r, val)
        self.assertNotIn(7, self.m)
        self.assertNotIn(7, self.m.map)


class SparseListTest(FlaskTestDB):

    def setUp(self):
        super(SparseListTest, self).setUp()
        self.s = SparseList()

    def test_create(self):
        self.assertEqual(self.s.index, 0)
        self.assertTrue(hasattr(self.s, 'items'))

    def test_append(self):
        r = self.s.append(7)
        self.assertEqual(self.s.index, 1)
        self.assertEqual(r, 0)
        self.assertEqual(self.s.items[r], 7)
        r = self.s.append(8)
        self.assertEqual(self.s.index, 2)
        self.assertEqual(r, 1)
        self.assertEqual(self.s.items[r], 8)

    def test_len(self):
        self.assertEqual(len(self.s), 0)
        self.s.append(1)
        self.assertEqual(len(self.s), 1)
        self.s.append(2)
        self.assertEqual(len(self.s), 2)
        self.s.append(2)
        self.assertEqual(len(self.s), 3)

    def test_getitem(self):
        self.s.append(7)
        self.assertEqual(self.s.items[0], 7)

    def test_setitem(self):
        self.s[8] = 10
        self.assertEqual(self.s[8], 10)

    def test_delitem(self):
        self.s[7] = 1
        self.assertEqual(self.s[7], 1)
        del self.s[7]
        self.assertRaises(KeyError, self.s.__getitem__, 7)

    def test_iter(self):
        self.s[7] = 1
        self.s[8] = 2
        self.assertEqual(list(self.s), [1, 2])

    def test_repr(self):
        self.s[7] = 1
        self.assertEqual(repr(self.s), repr([1]))

    def test_get(self):
        self.s[7] = 1
        self.assertEqual(self.s.get(7), 1)
        self.assertIs(self.s.get(1), None)

    def test_pop(self):
        self.s[7] = 1
        r = self.s.pop(7)
        self.assertEqual(r, 1)
        self.assertRaises(KeyError, self.s.__getitem__, 7)


class StrongholdTest(FlaskTestDBWorld):

    def setUp(self):
        super(StrongholdTest, self).setUp()
        self.w = self.world
        self.f = self.db['fields'][Hex(0, 0)]
        self.s = self.f.stronghold
        self.s.silo.imbue(create_comp(earth=128))

    def test_create(self):
        self.assertEqual(self.s.owner, self.f.owner)
        self.assertEqual(self.s.field, self.f)
        self.assertEqual(self.s.clock, self.f.clock)
        self.assertIs(self.s.stable, None)
        self.assertIs(self.s.armory, None)
        self.assertIs(self.s.farm, None)
        self.assertIsNot(self.s.home, None)

    def test_units(self):
        scients = []
        for i in xrange(6):
            scients.append(self.s.form_scient(E, create_comp(earth=i + 1)))
        self.s.form_squad(unit_ids=[u.uid for u in scients[2:4]])
        self.s.form_squad(unit_ids=[u.uid for u in scients[4:]])
        for s in scients:
            self.assertEqual(s, self.s.units.get(s.uid))

    def test_get(self):
        loc = Hex(0, 1)
        s = Stronghold.get(loc)
        self.assertTrue(s)
        self.assertEqual(s.field.world_coord, loc)

    def test_create_factory(self):
        # Maps attribute_name -> kinds
        c = dict(stable=['Stable', 'Earth'],
                 armory=['Armory', 'Fire'],
                 home=['Home', 'Ice'],
                 farm=['Farm', 'Wind'])

        # Clear anything set
        for key in c:
            # might as well check this...
            self.assertTrue(hasattr(self.s, key))
            setattr(self.s, key, None)

        for key, kinds in c.iteritems():
            for kind in kinds:
                # Setting once should be correct
                self.assertIs(getattr(self.s, key), None)
                self.s.create_factory(kind)
                self.assertIsNot(getattr(self.s, key), None)
                # Setting again should raise ValueError mentioning the kind
                self.assertExceptionContains(ValueError, kinds[0].lower(),
                                             self.s.create_factory, kind)
                # Reset
                setattr(self.s, key, None)

        # Invalid kind
        self.assertExceptionContains(ValueError, 'Unknown',
                                     self.s.create_factory, 'sdamdwadm')

    def test_form_weapon(self):
        self.assertExceptionContains(ValueError, 'weapon type',
                                     self.s.form_weapon, E,
                                     create_comp(earth=128), 'sadawdwa')
        self.assertExceptionContains(ValueError, 'element',
                                     self.s.form_weapon, 'xacscasc',
                                     create_comp(earth=128), 'Bow')
        weapon = self.s.form_weapon(E, create_comp(earth=1), 'Sword')
        self.assertIn(weapon, self.s.weapons)
        self.assertEqual(weapon.type, 'Sword')
        self.assertEqual(weapon.value(), 1)
        self.assertEqual(self.s.silo.value(), 127)

    def test_imbue_weapon(self):
        weapon = self.s.form_weapon(E, create_comp(earth=10), 'Sword')
        self.assertEqual(self.s.silo.value(), 118)
        self.assertEqual(weapon.value(), 10)
        weapon = self.s.imbue_weapon(create_comp(earth=5),
                                     weapon.stronghold_pos)
        self.assertEqual(weapon.value(), 15)
        self.assertEqual(self.s.silo.value(), 113)

    def test_split_weapon(self):
        weapon = self.s.form_weapon(E, create_comp(earth=10), 'Sword')
        self.assertEqual(self.s.silo.value(), 118)
        self.assertEqual(weapon.value(), 10)
        weapon = self.s.split_weapon(create_comp(earth=1),
                                     weapon.stronghold_pos)
        self.assertEqual(weapon.value(), 9)
        self.assertEqual(self.s.silo.value(), 119)

    def test_form_scient(self):
        self.assertEqual(self.s.silo.value(), 128)
        scient = self.s.form_scient(E, create_comp(earth=10), name='test')
        self.assertEqual(scient.container, self.s.free_units)
        self.assertEqual(scient.name, 'test')
        self.assertEqual(scient.value(), 10)
        self.assertEqual(self.s.silo.value(), 128 - scient.value() * 2)
        self.assertEqual(self.s.units[scient.uid], scient)
        self.assertEqual(self.s.free_units[scient.uid], scient)

    def test_name_unit(self):
        unit = self.s.form_scient(E, create_comp(earth=10), name='test')
        self.assertEqual(unit.name, 'test')
        self.s.name_unit(unit.uid, 'dog')
        self.assertEqual(unit.name, 'dog')

    def test_imbue_unit(self):
        unit = self.s.form_scient(E, create_comp(earth=10))
        self.assertEqual(unit.value(), 10)
        self.assertIsNot(unit.container, None)
        unit = self.s.imbue_unit(create_comp(earth=1), unit.uid)
        self.assertEqual(unit.value(), 11)
        self.assertEqual(self.s.silo.value(), 128 - 21)

        # test with unit in a squad instead of free
        squad = self.s.form_squad(unit_ids=[unit.uid])
        self.assertEqual(squad.value(), 11)
        unit = self.s.imbue_unit(create_comp(earth=1), unit.uid)
        self.assertEqual(unit.value(), 12)
        self.assertEqual(squad.value(), 12)
        self.assertEqual(self.s.silo.value(), 128 - 22)

    def test_equip_scient(self):
        unit = self.s.form_scient(E, create_comp(earth=10))
        self.assertIs(unit.weapon, None)
        weapon = self.s.form_weapon(E, create_comp(earth=1), 'Bow')
        self.s.equip_scient(unit.uid, weapon.stronghold_pos)
        self.assertEqual(unit.weapon, weapon)
        self.assertIs(weapon.stronghold, None)
        self.assertIs(weapon.stronghold_pos, None)
        old_weapon = weapon

        # Re-equipping should unequip previous
        weapon = self.s.form_weapon(E, create_comp(earth=2), 'Wand')
        self.s.equip_scient(unit.uid, weapon.stronghold_pos)
        self.assertEqual(unit.weapon, weapon)
        self.assertIs(weapon.stronghold, None)
        self.assertIs(weapon.stronghold_pos, None)
        self.assertIsNot(old_weapon.stronghold, None)
        self.assertIsNot(old_weapon.stronghold_pos, None)
        self.assertEqual(self.s.weapons.get(old_weapon.stronghold_pos),
                         old_weapon)

    def test_unequip_scient(self):
        unit = self.s.form_scient(E, create_comp(earth=10))
        weapon = self.s.form_weapon(E, create_comp(earth=1), 'Bow')
        self.s.equip_scient(unit.uid, weapon.stronghold_pos)
        self.assertIsNot(unit.weapon, None)
        self.s.unequip_scient(unit.uid)
        self.assertIs(unit.weapon, None)
        self.assertIsNot(weapon.stronghold, None)
        self.assertIsNot(weapon.stronghold_pos, None)
        self.assertEqual(self.s.weapons.get(weapon.stronghold_pos), weapon)

    def test_form_squad(self):
        ua = self.s.form_scient(E, create_comp(earth=10))
        ub = self.s.form_scient(E, create_comp(earth=10))
        self.assertIn(ua.uid, self.s.free_units)
        self.assertIn(ub.uid, self.s.free_units)
        self.assertIn(ua.uid, self.s.units)
        self.assertIn(ub.uid, self.s.units)
        sq = self.s.form_squad(unit_ids=(ua.uid, ub.uid), name='sq')
        self.assertEqual(sq.name, 'sq')
        self.assertIn(ua, sq)
        self.assertIn(ub, sq)
        self.assertEqual(len(sq), 2)
        self.assertNotIn(ua.uid, self.s.free_units)
        self.assertNotIn(ub.uid, self.s.free_units)
        self.assertIn(ua.uid, self.s.units)
        self.assertIn(ub.uid, self.s.units)
        self.assertIn(sq, self.s.squads)
        self.assertEqual(sq.stronghold, self.s)
        self.assertIsNot(sq.stronghold_pos, None)

    def test_form_squad_error(self):
        start_units = len(self.s.free_units)
        n_units = 20
        scients = [self.s.form_scient(E, create_comp(earth=1))
                   for i in range(n_units)]
        uids = [s.uid for s in scients]
        sq = self.s.form_squad(unit_ids=uids, name='sq')
        # squad should not be filled up
        self.assertLess(len(sq), n_units)
        self.assertEqual(len(self.s.free_units) - start_units,
                         n_units - len(sq))

    def test_name_squad(self):
        unit = self.s.form_scient(E, create_comp(earth=10))
        sq = self.s.form_squad(unit_ids=(unit.uid,), name='sq')
        self.assertEqual(sq.name, 'sq')
        self.s.name_squad(sq.stronghold_pos, 'xxx')
        self.assertEqual(sq.name, 'xxx')

    def test_remove_squad(self):
        unit = self.s.form_scient(E, create_comp(earth=10))
        sq = self.s.form_squad(unit_ids=(unit.uid,), name='sq')
        self.assertIn(sq, self.s.squads)
        sqq = self.s.remove_squad(sq.stronghold_pos)
        self.assertEqual(sq, sqq)

    def test_get_defenders(self):
        self.s._defenders = None
        self.assertIs(self.s.defenders, None)
        self.s._defenders = 0
        self.assertEqual(self.s.defenders, self.s.squads[0])

    def test_set_defenders(self):
        # Unset
        self.s.defenders = None
        self.assertIs(self.s.defenders, None)
        # Set by squad num
        self.s.defenders = 0
        self.assertEqual(self.s.defenders, self.s.squads[0])
        # Set by squad
        self.s.defenders = self.s.squads[0]
        self.assertEqual(self.s.defenders, self.s.squads[0])
        # Set with bad squad
        self.s.squads[0].stronghold = None
        self.assertRaises(ValueError, self.s.__setattr__, 'defenders',
                          self.s.squads[0])
        # Set with unknown squad num
        self.assertRaises(ValueError, self.s.__setattr__, 'defenders', 99)

    def test_api_view(self):
        schema = Schema(dict(field=tuple, silo=dict, weapons=[dict],
                             free_units=[dict], squads=[dict], defenders=dict))
        data = self.s.api_view()
        self.assertNotEqual(data['defenders'], {})
        self.assertValidSchema(data, schema)
        # Without defenders
        self.s.defenders = None
        data = self.s.api_view()
        self.assertEqual(data['defenders'], {})
        self.assertValidSchema(data, schema)
