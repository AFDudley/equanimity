from unittest import TestCase
from server import create_app
from server.utils import AttributeDict, construct_full_url


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
        app = create_app(subdomain='dog')
        self.assertTrue(app.config['SERVER_NAME'].startswith('dog'))
