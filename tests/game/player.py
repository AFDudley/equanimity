from ..base import FlaskTestDB, FlaskTestDBWorld
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


class PlayerTestWorld(FlaskTestDBWorld):

    def test_squads(self):
        player = Player('x', 'x', 'x')
        self.assertEqual(player.get_squads(self.world.uid), [])

        s = Scient(E, create_comp(earth=1))
        sqa = Squad(data=[s], owner=player)
        t = Scient(E, create_comp(earth=1))
        sqb = Squad(data=[t], owner=player)
        self.world.fields[(0, 0)].owner = player
        self.world.fields[(0, 1)].owner = player
        self.world.fields[(0, 0)].stronghold._add_squad(sqa)
        self.world.fields[(0, 1)].stronghold._add_squad(sqb)

        self.assertEqual(sorted(player.get_squads(self.world.uid)),
                         sorted([sqa, sqb]))


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
