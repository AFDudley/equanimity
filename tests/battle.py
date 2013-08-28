import itertools
from unittest import TestCase
from base import create_comp, FlaskTestDB
from server.utils import AttributeDict
from equanimity.grid import Grid, Loc, noloc
from equanimity.const import E, F
from equanimity.units import Scient
from equanimity.player import Player
from equanimity.helpers import rand_squad
from equanimity.unit_container import Squad
from equanimity.battle import (now, Action, Message, ChangeList, BattleChanges,
                               InitialState, Log, State, Game)


class ActionTest(TestCase):

    def test_create(self):
        a = Action()
        self.assertGreaterEqual(now(), a['when'])
        self.assertIs(a['target'], None)
        self.assertEqual(a['type'], 'pass')
        self.assertIs(a['unit'], None)
        self.assertIs(a['num'], None)
        return a


class MessageTest(TestCase):

    def test_create(self):
        m = Message(1, None)
        self.assertEqual(m['num'], 1)
        self.assertIs(m['result'], None)
        self.assertTrue(m['when'])


class ChangeListTest(TestCase):

    def test_create(self):
        c = ChangeList(None, something=1)
        self.assertEqual(c['something'], 1)
        self.assertIs(c['event'], None)


class BattleChangesTest(TestCase):

    def test_create(self):
        b = BattleChanges([0], [1], [2], event='test')
        self.assertEqual(b['event'], 'test')
        self.assertEqual(b['victors'], [0])
        self.assertEqual(b['prisoners'], [1])
        self.assertEqual(b['awards'], [2])


class InitialStateTest(TestCase):

    def test_create(self):
        player = AttributeDict(name='test')
        log = dict(players=[player], init_locs=1, start_time=now(), units=[2],
                   grid=None, owners=[7, 7])
        i = InitialState(log)
        self.assertEqual(i['player_names'], ('test',))
        for k, v in log.iteritems():
            if k != 'players':
                self.assertEqual(i[k], v)


class LogTest(FlaskTestDB):

    def test_create(self):
        log = Log([], [], Grid())
        self.assertTrue(log)
        keys = ['actions', 'applied', 'condition', 'change_list', 'event',
                'end_time', 'init_locs', 'messages', 'owners', 'start_time',
                'states', 'winner', 'world_coords', 'players', 'units', 'grid']
        for k in keys:
            self.assertIn(k, log)

    def test_init_locs(self):
        s = Scient(E, create_comp(earth=128))
        s.location = Loc(0, 0)
        log = Log([], {0: s}, Grid())
        locs = log.init_locs()
        self.assertEqual(locs[0], Loc(0, 0))

    def test_close(self):
        log = Log([], [], Grid())
        log.close('you', 'done')
        self.assertEqual(log['winner'], 'you')
        self.assertEqual(log['condition'], 'done')
        self.assertGreaterEqual(now(), log['end_time'])

    def test_get_owner(self):
        s = Scient(E, create_comp(earth=128))
        squad = Squad(name='test', data=[s])
        player = AttributeDict(squads=[squad])
        log = Log([player], {0: s}, Grid())
        owner = log.get_owner(0)
        self.assertEqual(owner, player)
        player.squads = []
        self.assertIs(log.get_owner(0), None)

    def test_get_owners(self):
        s = Scient(E, create_comp(earth=128))
        squad = Squad(name='test', data=[s])
        player = AttributeDict(squads=[squad], name='testplayer')
        log = Log([player], {0: s}, Grid())
        owners = log.get_owners()
        self.assertEqual(owners, {0: 'testplayer'})


class StateTest(FlaskTestDB):

    def setUp(self):
        super(StateTest, self).setUp()
        self.s = State()
        self.attacker = Player('Atk', 'x@gmail.com', 'xxx',
                               squads=[rand_squad()])
        defsquad = rand_squad()
        self.defender = Player('Def', 'y@gmail.com', 'xxx', squads=[defsquad])
        self.game = Game(self.attacker, self.defender)
        self.s['old_defsquad_hp'] = defsquad.hp()

    def assertGameOver(self, winner, condition):
        self.assertTrue(self.game.state['game_over'])
        self.assertEqual(self.game.winner, winner)
        self.assertEqual(self.game.log['condition'], condition)

    def _add_action(self, **action_kwargs):
        self.game.log['actions'].append(Action(**action_kwargs))

    def _add_actions(self, count, **action_kwargs):
        [self._add_action(**action_kwargs) for i in xrange(count)]

    def _check(self):
        self.s.check(self.game)

    def test_create(self):
        keys = ['HPs', 'queued', 'locs', 'num', 'pass_count', 'hp_count',
                'old_defsquad_hp', 'game_over', 'whose_action']
        for k in keys:
            self.assertIn(k, self.s)

    def test_check_single_action(self):
        self._add_action()
        self._check()
        self.assertEqual(self.s['pass_count'], 1)

    def test_check_nonpass_action(self):
        self._add_action(type='move')
        self._check()
        self.assertEqual(self.s['pass_count'], 0)

    def test_complete_turn_no_defender_damage(self):
        self.s['num'] = 4
        self.s['old_defsquad_hp'] = self.game.battlefield.defsquad.hp() - 1
        self._add_actions(4)
        self._check()
        self.assertEqual(self.s['hp_count'], 0)

    def test_complete_turn_defender_took_damage(self):
        self.game.battlefield.defsquad[0].hp = 0
        self._add_actions(4)
        self.s['num'] = 4
        self._check()
        self.assertEqual(self.s['hp_count'], 1)

    def test_game_over_not_enough_damage(self):
        # test for game over check, where attacker was not able to kill
        self._add_actions(4)
        for i in xrange(4):
            self.s['num'] = 4
            self.s['old_defsquad_hp'] *= 2
            self._check()
        self.assertEqual(self.s['hp_count'], 4)
        self.assertGameOver(self.defender,
                            'Attacker failed to deal sufficent damage.')

    def test_game_over_defenders_killed(self):
        # test for game over check, where defending squad is dead
        self._add_action()
        for squad in self.defender.squads:
            for unit in squad:
                unit.hp = 0
        self.s['old_defsquad_hp'] = 0
        self._check()
        self.assertGameOver(self.attacker, 'Defender\'s squad is dead')

    def test_game_over_attackers_killed(self):
        # test for game over check, where attacking squad is dead
        self._add_action()
        for squad in self.attacker.squads:
            for unit in squad:
                unit.hp = 0
        self.s['old_defsquad_hp'] = 0
        self._check()
        self.assertGameOver(self.defender, 'Attacker\'s squad is dead')

    def test_game_over_everyone_passed(self):
        # test for game over, where both sides passed
        self._add_actions(8)
        for i in xrange(8):
            self.s['num'] = i + 1
            self._check()
        self.assertGameOver(self.defender, 'Both sides passed')


class GameTest(FlaskTestDB):

    def setUp(self):
        super(GameTest, self).setUp()
        self.attacker = Player('Atk', 'x@gmail.com', 'xxx',
                               squads=[rand_squad(suit=E)])
        self.defender = Player('Def', 'y@gmail.com', 'yyy',
                               squads=[rand_squad(suit=F)])
        self.game = Game(self.attacker, self.defender)

    @property
    def units(self):
        return sorted(list(itertools.chain(self.attacker.squads[0],
                                           self.defender.squads[0])))

    def _place_squads(self):
        self.game.battlefield.rand_place_squad(self.attacker.squads[0])
        self.game.battlefield.rand_place_squad(self.defender.squads[0])
        self.game.put_squads_on_field()

    def test_create(self):
        self.assertEqual(self.game.attacker, self.attacker)
        self.assertEqual(self.game.defender, self.defender)
        self.assertEqual(sorted(set(self.game.log['owners'].values())),
                         sorted(['Atk', 'Def']))

    def test_put_squads_on_field(self):
        self._place_squads()
        self.assertTrue(self.game.log['init_locs'])
        for unit in self.units:
            self.assertIsNot(unit.location, None)
            self.assertNotEqual(unit.location, noloc)

    def test_unit_map(self):
        m = self.game.unit_map()
        self.assertEqual(sorted(m.keys()), self.units)
        self.assertEqual(sorted(m.values()), range(1, len(self.units) + 1))

    def test_map_unit(self):
        unit_map = self.game.unit_map()
        m = self.game.map_unit()
        self.assertEqual(sorted(m.keys()), sorted(unit_map.values()))
        self.assertEqual(sorted(m.values()), sorted(unit_map.keys()))

    def test_map_locs(self):
        self._place_squads()
        locs = self.game.map_locs()
        self.assertEqual(sorted(locs.keys()), sorted(self.game.units.keys()))
        self.assertEqual(sorted(locs.values()),
                         sorted([u.location for u in self.units]))

    def test_hps(self):
        self._place_squads()
        hps = self.game.HPs()
        self.assertEqual(sorted(hps.keys()), sorted(self.game.units.keys()))
        self.assertEqual(sorted(hps.values()),
                         sorted([u.hp for u in self.units]))

    def test_update_unit_info(self):
        self._place_squads()
        hps, locs = self.game.update_unit_info()
        self.assertEqual(hps, self.game.HPs())
        self.assertEqual(locs, self.game.map_locs())

    def test_map_queue(self):
        self._place_squads()
        dfdr = self.defender.squads[0][0]
        self.game.battlefield.dmg_queue[dfdr].append([100, 2])
        dmg_q = self.game.map_queue()
        self.assertTrue(dmg_q)
        self.assertIn(dfdr.id, dmg_q)
        for id, dmg in dmg_q.iteritems():
            if id == dfdr.id:
                self.assertEqual(dmg, [[100, 2]])
            else:
                self.assertEqual(dmg, [])

    def test_map_result(self):
        self._place_squads()
        dfdr = self.defender.squads[0][0]
        self.game.battlefield.dmg_queue[dfdr].append([1, 2])
        qd = self.game.battlefield.apply_queued()
        self.assertEqual(self.game.map_result(qd), [[dfdr.id, 1]])

    def test_map_action(self):
        d = self.defender.squads[0][0]
        act = self.game.map_action(unit=d)
        self.assertEqual(act['unit'], d.id)

    def test_last_message(self):
        self._place_squads()
        none = ['There was no message.']
        # No messages in log, at all
        self.assertEqual(self.game.last_message(), none)
        # No result in last message
        self.game.log['messages'].append(AttributeDict(result=None))
        self.assertEqual(self.game.last_message(), none)
        # A result in last message
        res = ['A message']
        self.game.log['messages'].append(AttributeDict(result=res))
        self.assertEqual(self.game.last_message(), res)

    def test_process_action(self):
        pass

    def test_apply_queued(self):
        pass

    def test_get_last_state(self):
        pass

    def test_get_states(self):
        pass

    def test_initial_state(self):
        pass

    def test_end(self):
        pass
