from equanimity.units import Scient
from equanimity.unit_container import Squad
from equanimity.player import Player, WorldPlayer, PlayerGroup
from equanimity.const import WORLD_UID, E
from ..base import FlaskTestDB, FlaskTestDBWorld, create_comp


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


class PlayerGroupTest(FlaskTestDB):

    def setUp(self):
        super(PlayerGroupTest, self).setUp()
        self.pg = PlayerGroup()
        self.p = Player('xxx', 'yyy@gmail.com', 'asdawdawdad')
        self.q = Player('xyyy', 'asdawd@gmail.com', 'adawdoadawd')

    def test_create(self):
        self.assertFalse(self.pg.players)
        self.assertIs(self.pg._leader, None)

    def test_has(self):
        self.assertFalse(self.pg.has(self.p))
        self.assertFalse(self.pg.has(0))
        self.pg.add(self.p)
        self.assertTrue(self.pg.has(self.p))
        self.assertTrue(self.pg.has(self.p.uid))

    def test_add_all(self):
        players = [self.p, self.q]
        self.assertFalse(self.pg.players)
        self.pg.add_all(players)
        self.assertEqual(players, self.pg.players.values())
        for p in players:
            self.assertTrue(self.pg.has(p))

    def test_add(self):
        self.assertFalse(self.pg.has(self.p))
        self.pg.add(self.p)
        self.assertTrue(self.pg.has(self.p))
        self.assertEqual(self.pg._leader, self.p)
        self.pg.add(self.q)
        self.assertEqual(self.pg._leader, self.p)

    def test_remove(self):
        self.test_add()
        self.pg.remove(self.p)
        self.assertFalse(self.pg.has(self.p))
        self.assertIs(self.pg._leader, None)

    def test_remove_dont_reset_leader(self):
        self.test_add()
        self.assertEqual(self.pg.get_leader(), self.p)
        self.pg.add(self.q)
        self.assertEqual(self.pg.get_leader(), self.p)
        self.assertTrue(self.pg.has(self.q))
        self.pg.remove(self.q)
        self.assertEqual(self.pg.get_leader(), self.p)
        self.assertFalse(self.pg.has(self.q))

    def test_set_leader(self):
        # unset
        self.assertIs(self.pg._leader, None)
        # first add, autoset
        self.pg.add(self.p)
        self.assertEqual(self.pg._leader, self.p)
        # unset
        self.pg.set_leader(None)
        self.assertIs(self.pg._leader, None)
        # force set
        self.pg.set_leader(self.p)
        self.assertEqual(self.pg._leader, self.p)
        # unset
        self.pg.set_leader(None)
        self.assertIs(self.pg._leader, None)
        # set by uid
        self.pg.set_leader(self.p.uid)
        self.assertEqual(self.pg._leader, self.p)

    def test_set_leader_bad(self):
        self.assertIs(self.pg._leader, None)
        self.assertExceptionContains(ValueError, 'Unknown player',
                                     self.pg.set_leader, self.p)

    def test_iter(self):
        self.test_add_all()
        self.assertEqual(list(iter(self.pg)), [self.p, self.q])

    def test_get_leader(self):
        self.pg.add(self.p)
        self.assertEqual(self.pg.get_leader(), self.p)

    def test_get_leader_no_leader_set(self):
        self.pg.add(self.p)
        self.pg.set_leader(None)
        self.assertIs(self.pg._leader, None)
        self.assertEqual(self.pg.get_leader(), self.p)

    def test_get_leader_no_world(self):
        wp = WorldPlayer.get_or_create()
        self.pg.add(wp)
        self.pg.add(self.p)
        self.pg.set_leader(wp)
        self.assertEqual(self.p, self.pg.get_leader(allow_world=False))
        self.pg.set_leader(None)
        self.assertEqual(self.p, self.pg.get_leader(allow_world=False))

    def test_get_leader_yes_world(self):
        wp = WorldPlayer.get_or_create()
        self.pg.add(wp)
        self.pg.add(self.p)
        self.pg.set_leader(wp)
        self.assertEqual(wp, self.pg.get_leader(allow_world=True))
        self.pg.set_leader(None)
        self.assertIs(self.pg._leader, None)
        self.assertEqual(self.p, self.pg.get_leader(allow_world=False))

    def test_get_leader_no_leader(self):
        wp = WorldPlayer.get_or_create()
        self.assertIs(self.pg.get_leader(), None)
        self.pg.add(wp)
        self.assertEqual(self.pg._leader, wp)
        self.assertIs(self.pg.get_leader(allow_world=False), None)
