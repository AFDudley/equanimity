from ..base import FlaskTestDB
from equanimity.units import Scient
from equanimity.unit_container import Squad
from equanimity.player import Player, WorldPlayer
from equanimity.const import WORLD_UID, E
from ..base import create_comp


class PlayerTest(FlaskTestDB):

    def test_get_player_bad_uid(self):
        player = Player.get('xxx')
        self.assertIs(player, None)

    def test_is_world(self):
        player = Player('x', 'x', 'x')
        self.assertFalse(player.is_world())

    def test_repr(self):
        player = Player('x', 'x', 'x')
        self.assertEqual(str(player), '<Player: 1>')

    def test_squads(self):
        player = Player('x', 'x', 'x')
        self.assertIs(player._squads, None)
        self.assertIs(player.squads, None)
        s = Scient(E, create_comp(earth=1))
        sq = Squad(data=[s])
        player.squads = [sq]
        self.assertIn(sq, player.squads)
        self.assertEqual(player.squads, [sq])
        self.assertEqual(sq.owner, player)
        self.assertEqual(s.owner, player)
        # If a unit has a different owner, and we put it in the player's squads
        # it should raise an Exception
        s.owner = Player('y', 'y', 'y')
        self.assertRaises(ValueError, setattr, player, 'squads', [sq])


class WorldPlayerTest(FlaskTestDB):

    def setUp(self):
        WorldPlayer._world = None
        super(WorldPlayerTest, self).setUp()

    def test_create(self):
        player = WorldPlayer()
        self.assertEqual(player.uid, WORLD_UID)
        player.persist()

    def test_is_world(self):
        player = WorldPlayer()
        self.assertTrue(player.is_world())

    def test_persist(self):
        player = WorldPlayer()
        player.persist()
        self.assertTrue(self.db['players'][0])
        self.assertEqual(self.db['players'][0].uid, player.uid)

    def test_get(self):
        p = WorldPlayer()
        p.persist()
        q = WorldPlayer.get()
        self.assertEqual(p, q)
