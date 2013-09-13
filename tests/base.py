import os
import transaction
from itertools import izip, tee
from unittest import TestCase
from mock import Mock
from flask import url_for, json
from voluptuous import Schema as JSONSchema, Invalid as InvalidJSONSchema
from formencode import variabledecode
from server import db, create_app
from equanimity.const import E
from equanimity.units import Scient
from equanimity.world import init_db


def create_comp(earth=0, wind=0, fire=0, ice=0):
    return dict(Earth=earth, Wind=wind, Fire=fire, Ice=ice)


def _scient(element=E, **comp_args):
    if not comp_args:
        comp_args['earth'] = 128
    return Scient(element, create_comp(**comp_args))


def pairwise(iterable):
    # See: http://docs.python.org/2/library/itertools.html#recipes
    "s -> (s0,s1), (s1,s2), (s2, s3), ..."
    a, b = tee(iterable)
    next(b, None)
    return izip(a, b)


class FlaskTest(TestCase):

    # If xhr is True, requests will add X-Requested-With and return response
    # with response.json set to parsed data
    xhr = True

    def setUp(self):
        self.old_env = os.environ.get('EQUANIMITY_SERVER_SETTINGS')
        self.app = create_app(config='test')
        self.app.testing = True
        self.client = self.app.test_client()
        self.client.__enter__()
        self._ctx = self.app.test_request_context()
        self._ctx.push()
        self.app.preprocess_request()

    def tearDown(self):
        if self.old_env is not None:
            os.environ['EQUANIMITY_SERVER_SETTINGS'] = self.old_env
        self.client.__exit__(None, None, None)
        if self._ctx is not None:
            self._ctx.pop()

    def get_html(self, *args, **kwargs):
        return self.get(*args, **kwargs).data

    def _get_method(self, method):
        methods = dict(GET=self.client.get, POST=self.client.post,
                       PUT=self.client.put, DELETE=self.client.delete)
        method = method.upper()
        if method not in methods:
            err = '"{0}" is not a valid method.'
            raise NotImplementedError(err.format(method))
        return methods[method]

    def request(self, method, endpoint, follow_redirects=True, params=None,
                data=None, headers=None, use_json=False, **kwargs):
        if params is None:
            params = {}
        if data is None:
            data = {}
        if headers is None:
            headers = {}
        if self.xhr:
            headers.setdefault('X-Requested-With', 'XMLHttpRequest')
        if use_json:
            kwargs['content_type'] = 'application/json'
            if data is None:
                data = {}
            data = json.dumps(data)
        else:
            data = variabledecode.variable_encode(data, add_repetitions=False)
        meth = self._get_method(method)
        url = url_for(endpoint, **params)
        resp = meth(url, data=data, headers=headers,
                    follow_redirects=follow_redirects, **kwargs)
        if self.xhr:
            try:
                resp.json = json.loads(resp.data)
            except ValueError:
                resp.json = None
        return resp

    def post(self, endpoint, follow_redirects=True, params=None, data=None,
             headers=None, use_json=False, **kwargs):
        return self.request('POST', endpoint, headers=headers, params=params,
                            data=data, follow_redirects=follow_redirects,
                            use_json=use_json, **kwargs)

    def get(self, endpoint, follow_redirects=True, params=None, data=None,
            headers=None, use_json=False, **kwargs):
        return self.request('GET', endpoint, headers=headers, params=params,
                            data=data, follow_redirects=follow_redirects,
                            use_json=use_json, **kwargs)

    def put(self, endpoint, follow_redirects=True, params=None, data=None,
            headers=None, use_json=False, **kwargs):
        return self.request('PUT', endpoint, headers=headers, params=params,
                            data=data, follow_redirects=follow_redirects,
                            use_json=use_json, **kwargs)

    def delete(self, endpoint, follow_redirects=True, params=None, data=None,
               headers=None, use_json=False, **kwargs):
        return self.request('DELETE', endpoint, headers=headers, params=params,
                            data=data, follow_redirects=follow_redirects,
                            use_json=use_json, **kwargs)

    def assertStatus(self, status_code, response):
        self.assertEqual(status_code, response.status_code)

    def assert200(self, response):
        self.assertStatus(200, response)

    def assert400(self, response):
        self.assertStatus(400, response)

    def assert401(self, response):
        self.assertStatus(401, response)

    def assert403(self, response):
        self.assertStatus(403, response)

    def assert404(self, response):
        self.assertStatus(404, response)

    def assert500(self, response):
        self.assertStatus(500, response)

    def assertExceptionContains(self, exc, submsg, f, *args, **kwargs):
        try:
            f(*args, **kwargs)
        except exc as e:
            self.assertIn(submsg, str(e))
        else:
            self.fail('{0} not raised'.format(exc.__name__))

    def assertNoException(self, exc, f, *args, **kwargs):
        try:
            f(*args, **kwargs)
        except exc as e:
            self.fail('Exception raised: {0} "{1}"'.format(type(e), e))

    def assertValidJSON(self, response, schema, **kwargs):
        self.assert200(response)
        self.assertValidSchema(response.json, schema, **kwargs)

    def assertValidSchema(self, obj, schema, required=None):
        if required is None:
            required = True
        self.assertNoException(InvalidJSONSchema,
                               JSONSchema(schema, required=required), obj)

    def assertAPIError(self, response, field=None, value=unicode,
                       fields=None, main=None):
        if fields is None:
            fields = {}
        if field is not None:
            if fields.get(field) is not None:
                raise UserWarning('Don\'t provide field if its in fields')
            fields[field] = value
        if main is None:
            main = []
        s = dict(errors=dict(main=main, fields=fields))
        self.assertValidJSON(response, s)

    def mock_response(self, content, status_code=200, ok=True):
        mock = Mock()
        mock.content = content
        mock.ok = ok
        mock.status_code = status_code
        mock.iter_content = lambda size: mock.content
        mock.json = lambda: json.loads(mock.content or '{}')
        return mock


class FlaskTestDB(FlaskTest):

    def setUp(self):
        super(FlaskTestDB, self).setUp()
        transaction.abort()
        init_db(reset=True)
        transaction.commit()
        self.db = db

    def tearDown(self):
        transaction.abort()
        super(FlaskTestDB, self).tearDown()
