from equanimity.grid import Hex
from equanimity.world import World
from equanimity.const import E
from equanimity.stronghold import Stronghold
from ..base import FlaskTestDB, create_comp


class StrongholdTest(FlaskTestDB):

    def setUp(self):
        super(StrongholdTest, self).setUp()
        self.w = World()
        self.w.create()
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
        pos = weapon.stronghold_pos
        self.s.equip_scient(unit.uid, pos)
        self.assertEqual(unit.weapon, weapon)
        self.assertIs(self.s.weapons.get(pos), None)
        old_weapon = weapon

        # Re-equipping should unequip previous
        weapon = self.s.form_weapon(E, create_comp(earth=2), 'Wand')
        self.s.equip_scient(unit.uid, weapon.stronghold_pos)
        self.assertEqual(unit.weapon, weapon)
        self.assertIs(self.s.weapons.get(weapon.stronghold_pos), None)
        self.assertEqual(self.s.weapons.get(old_weapon.stronghold_pos),
                         old_weapon)

    def test_unequip_scient(self):
        unit = self.s.form_scient(E, create_comp(earth=10))
        weapon = self.s.form_weapon(E, create_comp(earth=1), 'Bow')
        self.s.equip_scient(unit.uid, weapon.stronghold_pos)
        self.assertIsNot(unit.weapon, None)
        self.s.unequip_scient(unit.uid)
        self.assertIs(unit.weapon, None)
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
