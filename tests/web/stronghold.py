import uuid
from flask import json
from flask.ext.jsonrpc.proxy import ServiceProxy
from server import db
from users import UserTestMixin
from equanimity.const import E
from ..base import FlaskTestDBWorld, create_comp


class LocalServiceProxy(ServiceProxy):

    def __init__(self, client, *args, **kwargs):
        self.client = client
        super(LocalServiceProxy, self).__init__(*args, **kwargs)

    def send_payload(self, params):
        data = json.dumps({
            'jsonrpc': self.version,
            'method': self.service_name,
            'params': params,
            'id': str(uuid.uuid1())
        })
        r = self.client.post(self.service_url, method='POST', data=data,
                             headers={'Content-Type': 'application/json'})
        return r.data

    def __call__(self, *args, **kwargs):
        params = kwargs if len(kwargs) else args
        r = self.send_payload(params)
        return json.loads(r)


class RPCTestBase(FlaskTestDBWorld, UserTestMixin):

    def setUp(self):
        FlaskTestDBWorld.setUp(self)
        UserTestMixin.setUp(self)
        self.create_user()
        self.proxy = LocalServiceProxy(self.client, '/api',
                                       service_name='equanimity')
        me = db['players'][self.uid]
        self.world.award_field(me, (0, 0))

    def assertNoError(self, r):
        self.assertFalse(r.get('error'))

    def assertError(self, r, msg=None):
        err = r.get('error')
        self.assertIsNot(err, None)
        self.assertIn(msg, err['message'])


class StrongholdTest(RPCTestBase):

    def setUp(self):
        super(StrongholdTest, self).setUp()
        self.loc = (0, 0)
        self.f = db['fields'][self.loc]
        self.s = self.f.stronghold
        self.s.silo.imbue(create_comp(earth=128))

    def make_weapon(self, *args, **kwargs):
        return self.s.form_weapon(*args, **kwargs)

    def make_scient(self, *args, **kwargs):
        return self.s.form_scient(*args, **kwargs)

    def test_login_required(self):
        self.logout()
        unit = self.make_scient(E, create_comp(earth=1))
        r = self.proxy.name_unit(self.loc, unit.uid, 'testname')
        self.assertError(r, '401')

    def test_invalid_stronghold(self):
        r = self.proxy.name_unit((66, 77), 1, 'xxx')
        self.assertError(r, 'Invalid Stronghold')

    def test_invalid_owner(self):
        r = self.proxy.name_unit((0, 1), 1, 'xxx')
        self.assertError(r, 'You do not own this Stronghold')

    def test_name_unit(self):
        unit = self.make_scient(E, create_comp(earth=1))
        r = self.proxy.name_unit(self.loc, unit.uid, 'testname')
        self.assertNoError(r)
        self.assertNoError(r)
        unit = r['result'].get('unit')
        self.assertIsNot(unit, None)
        self.assertEqual(unit['name'], 'testname')

    def test_equip_scient(self):
        wep = self.make_weapon(E, create_comp(earth=1), 'Bow')
        name = 'xxSW'
        scient = self.make_scient(E, create_comp(earth=1), name=name)
        r = self.proxy.equip_scient(self.loc, scient.uid, wep.stronghold_pos)
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
        r = self.proxy.unequip_scient(self.loc, scient.uid)
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
        r = self.proxy.imbue_unit(self.loc, create_comp(earth=1), scient.uid)
        self.assertNoError(r)
        unit = r['result'].get('unit')
        self.assertIsNot(unit, None)
        self.assertEqual(sum(unit['comp'].values()), 2)
        self.assertEqual(unit['comp'][E], 2)

    def test_split_weapon(self):
        wep = self.make_weapon(E, create_comp(earth=2), 'Bow')
        self.assertEqual(wep.value(), 2)
        r = self.proxy.split_weapon(self.loc, create_comp(earth=1),
                                    wep.stronghold_pos)
        self.assertNoError(r)
        w = r['result'].get('weapon')
        self.assertIsNot(w, None)
        self.assertEqual(sum(w['comp'].values()), 1)
        self.assertEqual(w['comp'][E], 1)
        self.assertEqual(wep.value(), 1)

    def test_imbue_weapon(self):
        wep = self.make_weapon(E, create_comp(earth=1), 'Bow')
        self.assertEqual(wep.value(), 1)
        r = self.proxy.imbue_weapon(self.loc, create_comp(earth=1),
                                    wep.stronghold_pos)
        self.assertNoError(r)
        w = r['result'].get('weapon')
        self.assertIsNot(w, None)
        self.assertEqual(sum(w['comp'].values()), 2)
        self.assertEqual(w['comp'][E], 2)
        self.assertEqual(wep.value(), 2)

    def test_form_squad(self):
        s = self.make_scient(E, create_comp(earth=1), name='xxx')
        t = self.make_scient(E, create_comp(earth=1), name='yyy')
        r = self.proxy.form_squad(self.loc, [s.uid, t.uid])
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
        r = self.proxy.name_squad(self.loc, sq['stronghold_pos'], name)
        self.assertNoError(r)
        sq = r['result'].get('squad')
        self.assertIsNot(sq, None)
        self.assertEqual(sq['name'], name)

    def test_remove_squad(self):
        sq = self.test_form_squad()
        r = self.proxy.remove_squad(self.loc, sq['stronghold_pos'])
        self.assertNoError(r)
        squads = r['result'].get('squads')
        self.assertIsNot(squads, None)
        self.assertEqual(len(squads), 0)

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
