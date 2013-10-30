from mock import patch, Mock, MagicMock
from voluptuous import Schema
from equanimity.grid import Hex
from equanimity.const import E, F
from equanimity.stronghold import (Stronghold, MappedContainer, SparseList,
                                   SparseStrongholdList)
from equanimity.unit_container import Squad
from equanimity.units import Scient
from equanimity.player import WorldPlayer, Player
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
        self.assertEqual(self.s.index, r)
        self.assertEqual(r, 0)
        self.assertEqual(self.s.items[r], 7)
        r = self.s.append(8)
        self.assertEqual(self.s.index, r)
        self.assertEqual(r, 1)
        self.assertEqual(self.s.items[r], 8)

    def test_append_skip_indices(self):
        self.s[0] = 1
        self.s[1] = 2
        self.s[3] = 4
        i = self.s.append(777)
        self.assertEqual(i, 2)
        self.assertEqual(self.s[i], 777)
        i = self.s.append(888)
        self.assertEqual(i, 4)
        self.assertEqual(self.s[i], 888)

    def test_len(self):
        self.assertEqual(len(self.s), 0)
        self.s.append(1)
        self.assertEqual(len(self.s), 1)
        self.s.append(2)
        self.assertEqual(len(self.s), 2)
        self.s.append(2)
        self.assertEqual(len(self.s), 3)

    def test_bool(self):
        self.assertFalse(self.s)
        i = self.s.append(7)
        self.assertTrue(self.s)
        self.s.pop(i)
        self.assertFalse(self.s)

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


class SparseStrongholdListTest(FlaskTestDBWorld):

    def setUp(self):
        super(SparseStrongholdListTest, self).setUp()
        self.f = self.db['fields'][Hex(0, 0)]
        self.s = SparseStrongholdList(self.f.stronghold)

    def test_create(self):
        self.assertEqual(self.s.stronghold, self.f.stronghold)

    @patch('equanimity.unit_container.Squad.add_to_stronghold')
    def test_append(self, mock_add):
        s = Squad()
        i = self.s.append(s)
        mock_add.assert_called_once_with(self.f.stronghold, i)
        self.assertEqual(self.s[i], s)

    @patch('equanimity.unit_container.Squad.add_to_stronghold')
    def test_setitem(self, mock_add):
        s = Squad()
        self.s[1] = s
        mock_add.assert_called_once_with(self.f.stronghold, 1)
        self.assertEqual(self.s[1], s)

    def test_setitem_no_overwrite(self):
        p = self.s.append(Squad())
        self.assertExceptionContains(ValueError, 'Can\'t overwrite item',
                                     self.s.__setitem__, p, Squad())

    @patch('equanimity.unit_container.Squad.remove_from_stronghold')
    def test_pop(self, mock_remove):
        s = Squad()
        i = self.s.append(s)
        t = self.s.pop(i)
        self.assertEqual(s, t)
        self.assertNotIn(i, self.s)
        mock_remove.assert_called_once_with()

    @patch('equanimity.unit_container.Squad.remove_from_stronghold')
    def test_delitem(self, mock_remove):
        s = Squad()
        i = self.s.append(s)
        del self.s[i]
        mock_remove.assert_called_once_with()
        self.assertNotIn(i, self.s)


class StrongholdTest(FlaskTestDBWorld):

    def setUp(self):
        super(StrongholdTest, self).setUp()
        self.w = self.world
        self.f = self.db['fields'][Hex(0, 0)]
        self.s = self.f.stronghold
        self.s.silo.imbue(create_comp(earth=128))
        self.player = Player('P', 'p@gmail.com', 'ppp')

    def test_create(self):
        self.assertEqual(self.s.field, self.f)
        self.assertIs(self.s.stable, None)
        self.assertIs(self.s.armory, None)
        self.assertIs(self.s.farm, None)
        self.assertIsNot(self.s.home, None)

    def test_owner(self):
        self.assertEqual(self.s.owner, self.f.owner)

    def test_location(self):
        self.assertEqual(self.s.location, self.f.world_coord)

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
        self.s._setup_default_defenders()
        self.s._defenders = 0
        self.assertEqual(self.s.defenders, self.s.squads[0])

    def test_get_defenders_automatic_no_units(self):
        self.s._defenders = None
        self.assertExceptionContains(ValueError, 'No free units',
                                     getattr, self.s, 'defenders')

    def test_get_defenders_automatic_existing_squad(self):
        self.s._defenders = None
        self.s.silo.imbue(create_comp(earth=255))
        ua = self.s.form_scient(E, create_comp(earth=44))
        ub = self.s.form_scient(E, create_comp(earth=22))
        sqa = self.s.form_squad(unit_ids=(ua.uid, ub.uid), name='xxy')
        self.s.silo.imbue(create_comp(earth=255))
        ua = self.s.form_scient(E, create_comp(earth=44))
        ub = self.s.form_scient(E, create_comp(earth=23))
        sqb = self.s.form_squad(unit_ids=(ua.uid, ub.uid), name='xxy')
        self.assertEqual(self.s.squads[0], sqa)
        self.assertGreater(sqb.value(), self.s.squads[0].value())
        self.assertEqual(self.s.defenders, sqb)

    def test_get_defenders_automatic_creating_squad(self):
        self.s.silo.imbue(create_comp(earth=255))
        ua = self.s.form_scient(E, create_comp(earth=31))
        ub = self.s.form_scient(E, create_comp(earth=32))
        self.s._defenders = None
        print self.s.defenders.units
        self.assertEqual(self.s.defenders.units, [ub, ua])

    def test_set_defenders(self):
        sq = self.s._setup_default_defenders()
        self.assertEqual(self.s.defenders, sq)
        # Unset
        self.s.defenders = None
        self.assertIs(self.s._defenders, None)
        # Set by squad num
        self.s.defenders = 0
        self.assertEqual(self.s.defenders, self.s.squads[0])
        # Set by squad
        self.s.defenders = self.s.squads[0]
        self.assertEqual(self.s.defenders, self.s.squads[0])
        # Set with bad squad
        self.s.squads[0].stronghold = None
        self.assertExceptionContains(ValueError, 'must be in stronghold',
                                     self.s.__setattr__, 'defenders',
                                     self.s.squads[0])
        # Set with unknown squad num
        self.assertExceptionContains(ValueError, 'Unknown squad at',
                                     self.s.__setattr__, 'defenders', 99)

    def test_api_view(self):
        self.s._setup_default_defenders()
        schema = Schema(dict(field=tuple, silo=dict, weapons=[dict],
                             free_units=[dict], squads=[dict], defenders=dict))
        data = self.s.api_view()
        self.assertNotEqual(data['defenders'], {})
        self.assertValidSchema(data, schema)

    def test_add_squad(self):
        sq = Squad(owner=self.player)
        self.f.owner = self.player
        self.s._add_squad(sq)
        self.assertEqual(self.s.squads[0], sq)

    def test_add_squad_has_stronghold(self):
        sq = Squad(owner=self.player)
        sq.stronghold = 1
        self.f.owner = self.player
        self.assertExceptionContains(ValueError, 'in another stronghold',
                                     self.s._add_squad, sq)

    def test_add_squad_wrong_owner(self):
        sq = Squad(owner=WorldPlayer.get())
        self.f.owner = self.player
        self.assertExceptionContains(ValueError, 'does not have same owner',
                                     self.s._add_squad, sq)

    def test_add_squad_same_stronghold(self):
        s = Squad(owner=self.s.owner)
        s.stronghold = self.s
        self.assertExceptionContains(ValueError, 'same stronghold',
                                     self.s._add_squad, s)

    def test_move_squad_to_defenders(self):
        self.s._setup_default_defenders()
        self.s.remove_defenders()
        self.assertIs(self.s._defenders, None)
        self.s.move_squad_to_defenders(0)
        self.assertEqual(self.s.squads[0], self.s.defenders)

    def test_remove_defenders(self):
        self.s._setup_default_defenders()
        self.assertIsNot(self.s.defenders, None)
        self.s.remove_defenders()
        self.assertIs(self.s._defenders, None)

    def test_add_unit_to_defenders(self):
        self.s._setup_default_defenders()
        l = len(self.s.defenders)
        s = self.s.form_scient(E, create_comp(earth=1))
        self.s.add_unit_to_defenders(s.uid)
        self.assertEqual(len(self.s.defenders), l + 1)
        self.assertIn(s, self.s.defenders)

    def test_move_squad_in(self):
        s = Squad(owner=self.s.owner)
        s.stronghold_pos = 0
        mock_remove = Mock(side_effect=lambda x: setattr(s, 'stronghold',
                                                         None))
        s.stronghold = MagicMock(remove_squad=mock_remove)
        self.s.move_squad_in(s)
        self.assertEqual(s.stronghold, self.s)
        mock_remove.assert_called_once_with(0)

    def test_disband_squad(self):
        self.s.silo.imbue(create_comp(earth=100, fire=100))
        self.assertEqual(len(self.s.free_units), 0)
        s = self.s.form_scient(E, create_comp(earth=1))
        t = self.s.form_scient(F, create_comp(fire=1))
        self.assertEqual(len(self.s.free_units), 2)
        sq = self.s.form_squad(unit_ids=(s.uid, t.uid), name='test')
        self.assertEqual(len(self.s.free_units), 0)
        self.assertEqual(len(sq), 2)
        self.s.disband_squad(sq.stronghold_pos)
        self.assertEqual(len(sq), 0)
        self.assertIs(sq.stronghold, None)
        self.assertEqual(len(self.s.free_units), 2)

    @patch.object(Stronghold, '_add_unit_to')
    def test_add_unit_to_squad(self, mock_add):
        s = self.s._setup_default_defenders()
        self.s.add_unit_to_squad(0, 0)
        mock_add.assert_called_once_with(self.s, s, 0)

    @patch.object(Stronghold, '_remove_unit_from')
    def test_remove_unit_from_defenders(self, mock_remove):
        s = self.s._setup_default_defenders()
        self.s.remove_unit_from_defenders(0)
        mock_remove.assert_called_once_with(s, 0)

    @patch.object(Stronghold, '_remove_unit_from')
    def test_remove_unit_from_squad(self, mock_remove):
        s = self.s._setup_default_defenders()
        self.s.remove_unit_from_squad(s.stronghold_pos, 0)
        mock_remove.assert_called_once_with(s, 0)

    def test_remove_unit_from_stronghold(self):
        s = self.s.form_scient(E, create_comp(earth=1))
        self.assertEqual(self.s.free_units.map, {s.uid: s})
        self.s._remove_unit_from(self.s, s.uid)
        self.assertEqual(self.s.free_units.map, {})

    def test_remove_unit_from_unrelated(self):
        s = Scient(E, create_comp(earth=1))
        self.assertExceptionContains(ValueError, 'has no relation',
                                     self.s._remove_unit_from, Squad(), s.uid)

    def test_setup_default_defeneders_twice(self):
        self.s._setup_default_defenders()
        self.assertExceptionContains(ValueError, 'already set up',
                                     self.s._setup_default_defenders)
