from equanimity.const import E
from ..base import create_comp
from rpc_base import RPCTestBase


class StrongholdTest(RPCTestBase):

    service_name = 'stronghold'

    def test_login_required(self):
        self.logout()
        unit = self.make_scient(E, create_comp(earth=1))
        r = self.proxy.name_unit(self.world.uid, self.loc, unit.uid,
                                 'testname')
        self.assertError(r, '401')

    def test_invalid_stronghold(self):
        r = self.proxy.name_unit(self.world.uid, (66, 77), 1, 'xxx')
        self.assertError(r, 'Invalid Stronghold')

    def test_invalid_owner(self):
        r = self.proxy.name_unit(self.world.uid, (0, 1), 1, 'xxx')
        self.assertError(r, 'You do not own this Stronghold')

    def test_name_unit(self):
        unit = self.make_scient(E, create_comp(earth=1))
        r = self.proxy.name_unit(self.world.uid, self.loc, unit.uid,
                                 'testname')
        self.assertNoError(r)
        self.assertNoError(r)
        unit = r['result'].get('unit')
        self.assertIsNot(unit, None)
        self.assertEqual(unit['name'], 'testname')

    def test_equip_scient(self):
        wep = self.make_weapon(E, create_comp(earth=1), 'Bow')
        name = 'xxSW'
        scient = self.make_scient(E, create_comp(earth=1), name=name)
        r = self.proxy.equip_scient(self.world.uid, self.loc, scient.uid,
                                    wep.stronghold_pos)
        self.assertNoError(r)
        unit = r['result'].get('unit')
        self.assertIsNot(unit, None)
        self.assertEqual(unit['name'], name)
        self.assertIsNot(unit['weapon'], None)
        self.assertEqual(unit['weapon']['type'], 'Bow')
        self.assertIs(unit['weapon']['stronghold'], None)
        self.assertIs(unit['weapon']['stronghold_pos'], None)
        return scient, wep

    def test_unequip_scient(self):
        scient, _ = self.test_equip_scient()
        r = self.proxy.unequip_scient(self.world.uid, self.loc, scient.uid)
        self.assertNoError(r)
        # returns the unequipped weapon
        w = r['result'].get('weapon')
        self.assertIsNot(w, None)
        self.assertIsNot(w['stronghold'], None)
        self.assertIsNot(w['stronghold_pos'], None)
        self.assertEqual(list(w['stronghold']), list(self.loc))

    def test_imbue_unit(self):
        scient = self.make_scient(E, create_comp(earth=1))
        self.assertEqual(scient.value(), 1)
        r = self.proxy.imbue_unit(self.world.uid, self.loc,
                                  create_comp(earth=1), scient.uid)
        self.assertNoError(r)
        unit = r['result'].get('unit')
        self.assertIsNot(unit, None)
        self.assertEqual(sum(unit['comp'].values()), 2)
        self.assertEqual(unit['comp'][E], 2)

    def test_split_weapon(self):
        wep = self.make_weapon(E, create_comp(earth=2), 'Bow')
        self.assertEqual(wep.value(), 2)
        r = self.proxy.split_weapon(self.world.uid, self.loc,
                                    create_comp(earth=1), wep.stronghold_pos)
        self.assertNoError(r)
        w = r['result'].get('weapon')
        self.assertIsNot(w, None)
        self.assertEqual(sum(w['comp'].values()), 1)
        self.assertEqual(w['comp'][E], 1)
        self.assertEqual(wep.value(), 1)

    def test_imbue_weapon(self):
        wep = self.make_weapon(E, create_comp(earth=1), 'Bow')
        self.assertEqual(wep.value(), 1)
        r = self.proxy.imbue_weapon(self.world.uid, self.loc,
                                    create_comp(earth=1), wep.stronghold_pos)
        self.assertNoError(r)
        w = r['result'].get('weapon')
        self.assertIsNot(w, None)
        self.assertEqual(sum(w['comp'].values()), 2)
        self.assertEqual(w['comp'][E], 2)
        self.assertEqual(wep.value(), 2)

    def test_form_squad(self):
        s = self.make_scient(E, create_comp(earth=1), name='xxx')
        t = self.make_scient(E, create_comp(earth=1), name='yyy')
        r = self.proxy.form_squad(self.world.uid, self.loc, [s.uid, t.uid])
        self.assertNoError(r)
        sq = r['result'].get('squad')
        self.assertIsNot(sq, None)
        self.assertIsNot(sq['stronghold'], None)
        self.assertEqual(sorted([s.uid, t.uid]), sorted(sq['units']))
        self.assertEqual(list(sq['stronghold']), list(self.loc))
        self.assertIsNot(sq['stronghold_pos'], None)
        return sq

    def test_name_squad(self):
        sq = self.test_form_squad()
        name = sq['name'] * 2
        r = self.proxy.name_squad(self.world.uid, self.loc,
                                  sq['stronghold_pos'], name)
        self.assertNoError(r)
        sq = r['result'].get('squad')
        self.assertIsNot(sq, None)
        self.assertEqual(sq['name'], name)

    def test_remove_squad(self):
        # Make a squad
        sq = self.test_form_squad()
        # Count how many are in there
        r = self._make_proxy('info').stronghold(self.world.uid, self.loc)
        self.assertNoError(r)
        old_len = len(r['result']['stronghold']['squads'])
        # Remove that first squad
        r = self.proxy.remove_squad(self.world.uid, self.loc,
                                    sq['stronghold_pos'])
        self.assertNoError(r)
        squads = r['result'].get('squads')
        self.assertIsNot(squads, None)
        self.assertEqual(len(squads), old_len - 1)

    def test_place_unit(self):
        sq = self.test_form_squad()
        unit_id = sq['units'][0]
        loc = [1, 1]
        r = self.proxy.place_unit(unit_id, loc)
        self.assertNoError(r)
        unit = r['result'].get('unit')
        self.assertEqual(list(unit['chosen_location']), loc)

    def test_place_unit_no_squad(self):
        s = self.make_scient(E, create_comp(earth=1))
        r = self.proxy.place_unit(s.uid, [1, 1])
        self.assertError(r, 'isn\'t in a squad')

    def test_place_unit_no_stronghold(self):
        sq = self.test_form_squad()
        self.s.squads[sq['stronghold_pos']].stronghold = None
        self.s.squads[sq['stronghold_pos']].stronghold_pos = None
        r = self.proxy.place_unit(sq['units'][0], [1, 1])
        self.assertError(r, 'isn\'t in a stronghold')
