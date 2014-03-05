from mock import patch
from voluptuous import Schema
from equanimity.vestibule import Vestibule
from equanimity.player import Player
from equanimity.helpers import AttributeDict
from ..base import FlaskTestDB


class VestibuleTest(FlaskTestDB):

    def test_create(self):
        v = Vestibule()
        self.assertEqual(v.uid, 1)
        self.assertTrue(hasattr(v, 'players'))
        self.assertIs(v.world, None)

    def test_get(self):
        v = Vestibule()
        v.persist()
        self.assertEqual(Vestibule.get(v.uid), v)

    def test_api_view(self):
        # Empty vestibule
        v = Vestibule()
        s = Schema(dict(players=list, uid=int, leader=None, world=None))
        self.assertValidSchema(v.api_view(), s)
        # Our player should be in the players list now
        p = Player('xxx', 'yyy@gmail.com', 'sdadwadawda')
        v.players.add(p)
        s = Schema(dict(players=[p.uid], uid=int, leader=p.uid, world=None))
        self.assertValidSchema(v.api_view(), s)
        # World should be in the api view if set
        v.world = AttributeDict(uid=7)
        s = Schema(dict(players=[p.uid], uid=int, leader=p.uid, world=7))
        self.assertValidSchema(v.api_view(), s)

    def test_persist(self):
        v = Vestibule()
        self.assertNotIn(v.uid, self.db['vestibules'])
        v.persist()
        self.assertIn(v.uid, self.db['vestibules'])
        self.assertEqual(self.db['vestibules'][v.uid], v)

    def test_eq_ne(self):
        v = Vestibule()
        self.assertEqual(v, v)
        w = Vestibule()
        self.assertNotEqual(v, w)
        self.assertNotEqual(w, v)
        x = AttributeDict(uid=v.uid)
        self.assertNotEqual(v, x)

    @patch('equanimity.vestibule.World.start')
    @patch('equanimity.vestibule.World.persist')
    def test_start(self, mock_world_persist, mock_world_start):
        v = Vestibule()
        p = Player('xxx', 'yyy@gmail.com', 'sdadwadawda')
        v.players.add(p)
        w = v.start()
        self.assertIn(p.uid, w.players.players)
        self.assertEqual(w.uid, v.uid)
        mock_world_persist.assert_called_once_with()
        mock_world_start.assert_called_once_with()
