from mock import MagicMock
from unittest import TestCase
from equanimity.helpers import (validate_length, atomic, AttributeDict,
                                PersistentKwargs)
from ..base import BaseTest


class TestHelpers(BaseTest):

    def test_validate_length(self):
        validate_length([1], **dict(min=0, max=10))

    def test_validate_length_invalid(self):
        self.assertExceptionContains(
            ValueError, 'Invalid sequence length', validate_length, [1],
            **dict(min=2, max=4)
        )
        self.assertExceptionContains(
            ValueError, 'Invalid sequence length', validate_length, [1] * 5,
            **dict(min=2, max=4)
        )

    def test_atomic_calls_function(self):
        f = MagicMock(__name__='dog')
        atomic(f)(7)
        f.assert_called_once_with(7)


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

    def test_attribute_dict_hasattr(self):
        d = AttributeDict()
        self.assertFalse(hasattr(d, 'dog'))
        d.dog = 7
        self.assertTrue(hasattr(d, 'dog'))
        d['cat'] = 8
        self.assertTrue(hasattr(d, 'cat'))


class PersistentKwargsTest(TestCase):

    def test_persistent_kwargs(self):
        p = PersistentKwargs()
        p.x = 7
        self.assertEqual(p.x, 7)
        q = PersistentKwargs(x=7)
        self.assertEqual(q.x, 7)
        q._p_changed = 0
        q.x = 8
        self.assertEqual(q.x, 8)
