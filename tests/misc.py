import os
from unittest import TestCase
from mock import patch
from server import create_app, attach_loggers
from server.utils import AttributeDict, construct_full_url
from base import FlaskTest


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
        e = None
        try:
            app = create_app()
        except Exception as e:
            raise
        finally:
            if old is not None:
                os.environ['EQUANIMITY_SERVER_SETTINGS'] = old


class RequestFormDecodeTest(FlaskTest):

    @patch('server.variabledecode.variable_decode')
    def test_bad_request_form(self, mock_decode):
        mock_decode.side_effect = ValueError
        r = self.post('users.login')
        self.assert400(r)
