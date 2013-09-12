import os
from unittest import TestCase
from server import create_app, attach_loggers
from server.utils import (AttributeDict, construct_full_url, api_error,
                          RateLimit)
from ..base import FlaskTestDB


class AttributeDictTest(TestCase):

    def test_attribute_dict(self):
        d = AttributeDict()
        d['key'] = 'key'
        self.assertEqual(d.key, 'key')
        d.key = 'dog'
        self.assertEqual(d['key'], 'dog')

    def test_attribute_dict_error(self):
        d = AttributeDict()
        self.assertRaises(AttributeError, lambda: d.dog)


class UtilsTest(TestCase):

    def test_construct_full_url(self):
        target = 'http://example.com/'

        urls = ['example.com', 'example.com/', 'http://example.com/']
        for url in urls:
            self.assertEqual(target, construct_full_url(url))

        urls = [
            'example.com/static',
            'example.com/static/',
            'http://example.com/static',
            'http://example.com/static/',
        ]
        for url in urls:
            self.assertEqual(target + 'static/', construct_full_url(url))

        target = 'https://example.com/'
        self.assertEqual(target, construct_full_url('https://example.com/'))


class APIErrorTest(TestCase):

    def test_api_error(self):
        out = api_error('err')['errors']
        self.assertEqual(out, dict(main=['err'], fields={}))
        out = api_error({'err': 'xxx'})['errors']
        self.assertEqual(out, dict(main=[], fields={'err': 'xxx'}))
        out = api_error(['err', 'xxx'])['errors']
        self.assertEqual(out, dict(main=['err', 'xxx'], fields={}))


class AppInitTest(TestCase):

    def test_subdomain_create_app(self):
        app = create_app(subdomain='dog', config='test')
        self.assertTrue(app.config['SERVER_NAME'].startswith('dog'))

    def test_logger_setup_no_debug(self):
        # There's nothing to really test besides to make sure the code
        # doesn't crash.  This only affects the logging levels set
        app = create_app(config='test')
        app.config['DEBUG'] = False
        app.config['DEBUG_LOGGING'] = False
        attach_loggers(app)

    def test_envvar_config_load(self):
        old = os.environ.get('EQUANIMITY_SERVER_SETTINGS')
        os.environ['EQUANIMITY_SERVER_SETTINGS'] = '../config/test.py'
        try:
            create_app()
        except Exception:
            raise
        finally:
            if old is not None:
                os.environ['EQUANIMITY_SERVER_SETTINGS'] = old

    def test_config_dev_default_load(self):
        old = os.environ.get('EQUANIMITY_SERVER_SETTINGS')
        if old is not None:
            del os.environ['EQUANIMITY_SERVER_SETTINGS']
        try:
            create_app(config=None)
        except Exception:
            raise
        finally:
            if old is not None:
                os.environ['EQUANIMITY_SERVER_SETTINGS'] = old


class RateLimitTest(FlaskTestDB):

    key = 'key'

    def setUp(self):
        super(RateLimitTest, self).setUp()

    def test_rate_limit_object(self):
        r = RateLimit(self.key, 10, 100)
        self.assertIn(self.key, r.key)
        self.assertEqual(r.limit, 10)
        self.assertEqual(r.per, 100)
        self.assertEqual(r.current, 1)
        self.assertFalse(r.over_limit)
        self.assertEqual(r.remaining, 9)

        r = RateLimit(self.key, 10, 100)
        self.assertEqual(r.current, 2)
        self.assertFalse(r.over_limit)
        self.assertEqual(r.remaining, 8)

        r.current = 10
        self.assertTrue(r.over_limit)
        self.assertEqual(r.remaining, 0)
