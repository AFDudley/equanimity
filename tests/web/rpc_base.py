from uuid import uuid1
from flask.ext.jsonrpc.proxy import ServiceProxy
from flask import json
from users import UserTestMixin
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
            'id': str(uuid1())
        })
        r = self.client.post(self.service_url, method='POST', data=data,
                             headers={'Content-Type': 'application/json'})
        return r.data

    def __call__(self, *args, **kwargs):
        params = kwargs if len(kwargs) else args
        r = self.send_payload(params)
        return json.loads(r)


class RPCTestBase(FlaskTestDBWorld, UserTestMixin):

    service_name = None

    def setUp(self):
        FlaskTestDBWorld.setUp(self, create_world=False)
        UserTestMixin.setUp(self)
        self.create_user()
        self.create_world(init_db_reset=False)
        self._proxy = None
        me = self.db['players'][self.uid]
        self.world.award_field(me, (0, 0))
        self.loc = (0, 0)
        self.f = self.db['fields'][self.loc]
        self.field = self.f
        self.s = self.f.stronghold
        self.s.silo.imbue(create_comp(earth=128))

    @property
    def proxy(self):
        if self._proxy is not None:
            return self._proxy
        if self.service_name is None:
            raise UserWarning('Must set service_name on the test class')
        self._proxy = LocalServiceProxy(self.client, '/api',
                                        service_name=self.service_name)
        return self._proxy

    def assertNoError(self, r):
        self.assertFalse(r.get('error'))

    def assertError(self, r, msg=None):
        err = r.get('error')
        self.assertIsNot(err, None)
        self.assertIn(msg, err['message'])

    def make_weapon(self, *args, **kwargs):
        return self.s.form_weapon(*args, **kwargs)

    def make_scient(self, *args, **kwargs):
        return self.s.form_scient(*args, **kwargs)
