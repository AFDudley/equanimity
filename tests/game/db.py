from unittest import TestCase
from equanimity.db import AutoID


class AutoIDTest(TestCase):

    def test_create(self):
        aid = AutoID('test')
        self.assertEqual(aid.name, 'test')
        self.assertEqual(aid.uid, 0)

    def test_get_next_id(self):
        aid = AutoID('test')
        self.assertEqual(aid.get_next_id(), 1)
        self.assertEqual(aid.get_next_id(), 2)
        self.assertEqual(aid.get_next_id(), 3)

    def test_str(self):
        aid = AutoID('test')
        aid.get_next_id()
        aid.get_next_id()
        self.assertEqual(str(aid), '<AutoID test [2]>')
