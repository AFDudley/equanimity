from equanimity.vestibule import Vestibule
from server.rpc.vestibule import _get_vestibule
from ..base import FlaskTestDB
from users import UserTestMixin
from rpc_base import RPCTestBase
from mock import patch
from mockredis import redis

class VestibuleToolsTest(FlaskTestDB, UserTestMixin):

    def setUp(self):
        FlaskTestDB.setUp(self)
        UserTestMixin.setUp(self)
        self.create_user()
        self.login()
        self.v = Vestibule()
        self.v.persist()

    def test_get_vestibule(self):
        v = _get_vestibule(self.v.uid)
        self.assertEqual(v, self.v)

    def test_get_vestibule_is_member(self):
        self.assertExceptionContains(ValueError, 'is not in vestibule',
                                     _get_vestibule, self.v.uid,
                                     is_member=True)
        self.v.players.add(self.get_user())
        self.assertEqual(self.v, _get_vestibule(self.v.uid, is_member=True))

    def test_get_vestibule_is_not_member(self):
        self.assertEqual(self.v, _get_vestibule(self.v.uid, is_member=False))
        self.v.players.add(self.get_user())
        self.assertExceptionContains(ValueError, 'is in vestibule',
                                     _get_vestibule, self.v.uid,
                                     is_member=False)

    def test_get_vestibule_no_world(self):
        self.v.world = 1
        self.assertExceptionContains(ValueError, 'already has a World',
                                     _get_vestibule, self.v.uid)

    def test_get_vestibule_ignore_world(self):
        self.v.world = 1
        self.assertEqual(self.v, _get_vestibule(self.v.uid, no_world=False))


class VestibuleTest(RPCTestBase):

    service_name = 'vestibule'

    def test_create_vestibule(self):
        v = self.proxy.create()
        self.assertNoError(v)
        v = v['result']['vestibule']
        self.assertEqual(v['leader'], self.player.uid)
        self.assertIn(self.player.uid, v['players'])
        return v

    def test_join_vestibule(self):
        user = dict(username='xcascasc', email='xxasd@gmail.com',
                    password='asdawdawd2d2da')
        p = self.create_user(data=user)
        v = self.proxy.create()
        self.assertNoError(v)
        v = v['result']
        self.assertEqual(p.json['uid'], v['vestibule']['leader'])
        self.login()
        r = self.proxy.join(v['vestibule']['uid'])
        self.assertNoError(r)
        r = r['result']
        self.assertIn(self.uid, r['vestibule']['players'])
        self.assertNotEqual(self.uid, r['vestibule']['leader'])
        self.assertEqual(v['vestibule']['uid'], r['vestibule']['uid'])
        return r['vestibule']

    def test_join_vestibule_already_in(self):
        v = self.test_create_vestibule()
        r = self.proxy.join(v['uid'])
        self.assertError(r)

    def test_leave_vestibule(self):
        v = self.test_join_vestibule()
        r = self.proxy.leave(v['uid'])
        self.assertNoError(r)
        v = r['result']['vestibule']
        self.assertNotIn(self.uid, v['players'])

    def test_leave_vestibule_not_in(self):
        v = self.test_create_vestibule()
        r = self.proxy.leave(v['uid'])
        self.assertNoError(r)
        r = self.proxy.leave(v['uid'])
        self.assertError(r)

    @patch('redis.Redis')
    def test_start_vestibule(self, mock_redis_client):
        v = self.test_create_vestibule()
        r = self.proxy.start(v['uid'])
        self.assertNoError(r)
        return v

    def test_start_vestibule_already_started(self):
        v = self.test_start_vestibule()
        r = self.proxy.start(v['uid'])
        self.assertError(r)

    def test_start_vestibule_not_leader(self):
        v = self.test_join_vestibule()
        r = self.proxy.start(v['uid'])
        self.assertError(r)

    def test_get_vestibule(self):
        v = self.test_create_vestibule()
        r = self.proxy.get(v['uid'])
        self.assertNoError(r)
        self.assertEqual(r['result']['vestibule'], v)

    def test_list_vestibules(self):
        a = self.test_create_vestibule()
        b = self.test_create_vestibule()
        r = self.proxy.list()
        self.assertNoError(r)
        self.assertEqual(sorted([a, b]), sorted(r['result']['vestibules']))
