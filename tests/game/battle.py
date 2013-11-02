import itertools
from unittest import TestCase
from mock import MagicMock, patch
from datetime import timedelta, datetime
from ..base import create_comp, FlaskTestDB, FlaskTestDBWorld, pairwise
from server.utils import AttributeDict
from equanimity.grid import Grid, Hex
from equanimity.const import E, F, PLY_TIME
from equanimity.weapons import Sword
from equanimity.units import Scient
from equanimity.field import Field
from equanimity.stone import Stone
from equanimity.player import Player
from equanimity.unit_container import Squad, rand_squad
from equanimity.battle import (now, Action, Message, ChangeList, BattleChanges,
                               InitialState, Log, State, Game, BattleError)


class ActionTest(TestCase):

    def test_create(self):
        a = Action()
        self.assertGreaterEqual(now(), a['when'])
        self.assertTrue(a['target'].is_null())
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


class BattleTestBase(FlaskTestDBWorld):
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


class GameTestBase(BattleTestBase):

    def setUp(self):
        super(GameTestBase, self).setUp()
        self._setup_game()

    def _setup_game(self, atksquad=None, defsquad=None, element=None):
        if atksquad is None:
            atksquad = rand_squad(suit=E)
        if defsquad is None:
            defsquad = rand_squad(suit=F)
        self.attacker = Player('Atk', 'x@gmail.com', 'xxx')
        self.defender = Player('Def', 'y@gmail.com', 'yyy')
        atksquad.owner = self.attacker
        defsquad.owner = self.defender
        f = Field((0, 0), owner=self.defender)
        self.field = self.db['fields'][(0, 0)]
        self.field.owner = self.defender
        self.field.stronghold._add_squad(defsquad)
        self.field.stronghold.defenders = defsquad
        f = self.db['fields'][(0, 1)]
        f.owner = self.attacker
        f.stronghold._add_squad(atksquad)
        self.game = Game(self.field, atksquad)
        self.commit()

    @property
    def bf(self):
        return self.game.battlefield

    @property
    def f(self):
        return self.game.field

    @property
    def units(self):
        return sorted(list(itertools.chain(self.defender.squads[0],
                                           self.attacker.squads[0])))

    def _place_squads(self):
        self.f.rand_place_squad(self.attacker.squads[0])
        self.f.rand_place_squad(self.defender.squads[0])
        self.game.start()


class LogTest(FlaskTestDB):

    def test_create(self):
        log = Log([], {}, Grid())
        self.assertTrue(log)
        keys = ['actions', 'applied', 'condition', 'change_list', 'event',
                'end_time', 'init_locs', 'messages', 'owners', 'start_time',
                'states', 'winner', 'world_coords', 'players', 'units', 'grid']
        for k in keys:
            self.assertIn(k, log)

    def test_init_locs(self):
        s = Scient(E, create_comp(earth=128))
        s.owner = Player('testplayer', 't@gmail.com', 'xxx')
        s.location = Hex(0, 0)
        log = Log([], {0: s}, Grid())
        log.init_locs()
        self.assertEqual(log['init_locs'][0], Hex(0, 0))

    def test_close(self):
        log = Log([], {}, Grid())
        log.close('you', 'done')
        self.assertEqual(log['winner'], 'you')
        self.assertEqual(log['condition'], 'done')
        self.assertGreaterEqual(now(), log['end_time'])

    def test_get_owner(self):
        s = Scient(E, create_comp(earth=128))
        player = Player('testplayer', 't@gmail.com', 'xxx')
        Squad(name='test', data=[s], owner=player)
        log = Log([player], {0: s}, Grid())
        owner = log.get_owner(0)
        self.assertEqual(owner, 'testplayer')

    def test_get_owners(self):
        s = Scient(E, create_comp(earth=128))
        player = Player('testplayer', 't@gmail.com', 'xxx')
        Squad(name='test', data=[s], owner=player)
        log = Log([player], {0: s}, Grid())
        owners = log.get_owners()
        self.assertEqual(owners, {0: 'testplayer'})

    @patch.object(Log, 'get_last_terminating_action_time')
    @patch('equanimity.battle.now')
    def test_get_time_remaining_for_action(self, mock_now, mock_term):
        log = Log([], {}, Grid())
        n = now()
        mock_now.return_value = n
        then = n - timedelta(minutes=1)
        mock_term.return_value = then
        self.assertEqual(log.get_time_remaining_for_action(), n - then)

    @patch.object(Log, 'get_last_terminating_action_time')
    def test_get_time_remaining_for_action_expired(self, mock_term):
        log = Log([], {}, Grid())
        n = now()
        then = n - (PLY_TIME * 10)
        mock_term.return_value = then
        self.assertEqual(log.get_time_remaining_for_action().seconds, 0)


class LogTestAdvanced(GameTestBase):

    def test_last_message(self):
        self._place_squads()
        none = ['There was no message.']
        # No messages in log, at all
        self.assertEqual(self.game.log.last_message(), none)
        # No result in last message
        self.game.log['messages'].append(AttributeDict(result=None))
        self.assertEqual(self.game.log.last_message(), none)
        # A result in last message
        res = ['A message']
        self.game.log['messages'].append(AttributeDict(result=res))
        self.assertEqual(self.game.log.last_message(), res)


class StateTest(BattleTestBase):

    def setUp(self):
        super(StateTest, self).setUp()
        self.attacker = Player('Atk', 'x@gmail.com', 'xxx')
        atksquad = rand_squad()
        atksquad.owner = self.attacker
        self.defender = Player('Def', 'y@gmail.com', 'xxx')
        defsquad = rand_squad()
        defsquad.owner = self.defender
        self.field = self.db['fields'][(0, 0)]
        self.field.owner = self.defender
        self.field.stronghold._add_squad(defsquad)
        f = self.db['fields'][(0, 1)]
        f.owner = self.attacker
        f.stronghold._add_squad(atksquad)
        self.game = Game(self.field, atksquad)
        self.s = State(self.game)
        self.s['old_defsquad_hp'] = defsquad.hp()

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


class GameTest(GameTestBase):

    def setUp(self):
        super(GameTest, self).setUp()

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
            self.assertNotEqual(unit.location, Hex.null)

    def test_unit_map(self):
        self.maxDiff = None
        m = self.game.unit_map()
        self.assertEqual(sorted(m.keys()), sorted(self.units))
        expect_ids = sorted([unit.uid for unit in self.units])
        self.assertEqual(sorted(m.values()), expect_ids)

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
        self.bf.dmg_queue[dfdr].append([100, 2])
        dmg_q = self.game.map_queue()
        self.assertTrue(dmg_q)
        self.assertIn(dfdr.uid, dmg_q)
        for uid, dmg in dmg_q.iteritems():
            if uid == dfdr.uid:
                self.assertEqual(dmg, [[100, 2]])
            else:
                self.assertEqual(dmg, [])

    def test_map_result(self):
        self._place_squads()
        dfdr = self.defender.squads[0][0]
        self.bf.dmg_queue[dfdr].append([1, 2])
        qd = self.bf.apply_queued()
        self.assertEqual(self.game.map_result(qd), [[dfdr.uid, 1]])

    def test_map_action(self):
        d = self.defender.squads[0][0]
        act = self.game.map_action(unit=d)
        self.assertEqual(act['unit'], d.uid)

    def test_apply_queued(self):
        self._place_squads()
        self._add_actions(4)
        dfdr = self.defender.squads[0][0]
        self.bf.dmg_queue[dfdr].append([1, 2])
        self.assertFalse(self.game.log['applied'])
        self.game.apply_queued()
        self.assertTrue(self.game.log['applied'])

    def test_get_last_state(self):
        self.game.log['states'] = [1]
        self.assertEqual(self.game.get_last_state(), 1)
        self.game.log['states'] = []
        self.assertIs(self.game.get_last_state(), None)
        del self.game.log['states']
        self.assertIs(self.game.get_last_state(), None)

    def test_get_states(self):
        self.game.log['states'] = [1]
        self.assertEqual(self.game.get_states(), [1])
        del self.game.log['states']
        self.assertIs(self.game.get_states(), None)

    def test_initial_state(self):
        init_state = self.game.initial_state()
        self.assertTrue(isinstance(init_state, InitialState))

    def test_compute_award(self):
        self.defender.squads[0][0].hp = 0
        comp = self.defender.squads[0][0].copy()
        wep_comp = Stone(create_comp(earth=2))
        weapon = Sword(E, wep_comp)
        wep_comp = wep_comp.copy().extract_award()
        self.defender.squads[0][0].equip(weapon)
        awards = self.game.compute_awards()
        comp = comp.extract_award()
        self.assertEqual(awards, [comp, wep_comp])

    @patch('equanimity.silo.Silo.imbue_list')
    @patch.object(Game, 'compute_awards')
    def test_end(self, mock_compute_awards, mock_imbue):
        awards = [Stone(create_comp(earth=2, ice=3, fire=1, wind=7))]
        mock_compute_awards.return_value = awards
        self._place_squads()
        self.game.winner = self.defender
        def_survivors = self.defender.squads[0][:2]
        atk_survivors = self.attacker.squads[0][:1]
        survivors = def_survivors + atk_survivors
        hps = {unit: unit.hp for unit in survivors}
        self.game.state = State(self.game, HPs=hps)
        self.game.end('Defender won')
        self.assertGameOver(self.defender, 'Defender won')
        self.assertEqual(sorted(def_survivors),
                         sorted(self.game.log['change_list']['victors']))
        self.assertEqual(sorted(atk_survivors),
                         sorted(self.game.log['change_list']['prisoners']))
        mock_compute_awards.assert_called_once_with()
        mock_imbue.assert_called_once_with(awards)


class BattleProcessActionTest(GameTestBase):

    def setUp(self):
        super(BattleProcessActionTest, self).setUp()

    @property
    def d(self):
        return self.defender.squads[0][0]

    @property
    def a(self):
        return self.attacker.squads[0][0]

    @property
    def past(self):
        return datetime.utcnow() - PLY_TIME - timedelta(minutes=5)

    def unit(self, num):
        return self.game.action_queue.get_unit_for_action(num)

    def assertActionResult(self, result, num, type, msg=None, target=Hex.null,
                           unit=None):
        if num % 4:
            self.assertNotIn('applied', result)
        else:
            self.assertIn('applied', result)
        self.assertEqual(result['command']['num'], num)
        self.assertEqual(result['command']['type'], type)
        self.assertEqual(result['command']['target'], target)
        self.assertEqual(result['command']['unit'], unit)
        self.assertEqual(result['response']['num'], num)
        if msg is not None:
            self.assertEqual(result['response']['result'], [[msg]])

    def test_doing_nothing(self):
        # with no unit, no prev_unit, no prev_act, passing
        act = Action()
        self.game.state = State(self.game, num=1)
        ret = self.game.process_action(act)
        self.assertActionResult(ret, 1, 'pass', 'Action Passed.')

    def test_timeout_first_action_start_time(self):
        self.game.log['start_time'] = self.past
        act = Action(type='move', num=1, unit=self.unit(1))
        self.game.state = State(self.game, num=1)
        ret = self.game._process_action(act)
        self.assertActionResult(ret, 1, 'timed_out', 'Failed to act.',
                                unit=self.unit(1).uid)

    def test_timeout_second_action_start_time(self):
        self.game.log['start_time'] = self.past
        act = Action(type='move', unit=self.unit(2))
        self.game.state = State(self.game, num=2)
        self.game.log['actions'] = [Action(num=1, unit=self.unit(1))]
        ret = self.game._process_action(act)
        self.assertActionResult(ret, 2, 'timed_out', 'Failed to act.',
                                unit=self.unit(2).uid)

    def test_timeout_first_action_after_other_action(self):
        act = Action(type='move', unit=self.unit(3))
        self.game.state = State(self.game, num=3)
        self.game.log['actions'] = [Action(unit=self.unit(1), when=self.past),
                                    Action(unit=self.unit(2), when=self.past)]
        ret = self.game._process_action(act)
        self.assertActionResult(ret, 3, 'timed_out', 'Failed to act.',
                                unit=self.unit(3).uid)

    def test_timeout_second_action_after_other_action(self):
        act = Action(type='move', num=4, unit=self.unit(4))
        self.game.state = State(self.game, num=4)
        self.game.log['actions'] = [Action(unit=self.unit(1), num=1,
                                           when=self.past),
                                    Action(unit=self.unit(2), num=2,
                                           when=self.past),
                                    Action(unit=self.unit(3), num=3)]
        ret = self.game._process_action(act)
        self.assertActionResult(ret, 4, 'timed_out', 'Failed to act.',
                                unit=self.unit(4).uid)

    def test_timed_out_action(self):
        act = Action(type='timed_out')
        self.game.state = State(self.game, num=1)
        ret = self.game.process_action(act)
        self.assertActionResult(ret, 1, 'timed_out', 'Failed to act.')

    def test_fill_timed_out_actions(self):
        start = self.game.log['start_time']
        self.game.log['start_time'] = start - PLY_TIME * 3 - PLY_TIME / 2
        self.game._fill_timed_out_actions()
        actions = self.game.log['actions']
        n = 6
        self.assertEqual(self.game.state['num'], n + 1)
        self.assertEqual(len(actions), n)
        # All numbers should be in sequence
        for n, act in enumerate(actions):
            self.assertEqual(n + 1, act['num'])
            # same ply whens should be equal
            if n % 2:
                self.assertEqual(act['when'], actions[n - 1]['when'])
        # All times should be ascending
        for i in reversed(range(1, n)):
            self.assertGreaterEqual(actions[i]['when'],
                                    actions[i - 1]['when'])
        # All times should definitely be greater across plies
        for i in reversed(range(3, n, 2)):
            self.assertGreater(actions[i]['when'], actions[i - 2]['when'])
        # Processing an action should work as expected
        act = Action(type='pass', unit=self.unit(7))
        ret = self.game.process_action(act)
        self.assertActionResult(ret, 7, 'pass', 'Action Passed.',
                                unit=self.unit(7).uid)

    def test_using_different_units(self):
        # get a ValueError by using two different units in a row
        act = Action(type='move', num=2, unit=self.unit(2))
        self.game.state = State(self.game, num=2)
        self.game.log['actions'] = [Action(num=4, unit=self.unit(4))]
        self.assertExceptionContains(BattleError,
                                     'Unit from the previous action',
                                     self.game.process_action, act)

    def test_first_movement(self):
        # do a legitimate movement, on a first action
        d = self.unit(1)
        d.chosen_location = Hex(0, 0)
        self.bf.place_object(d)
        loc = Hex(0, 1)
        act = Action(type='move', unit=d, target=loc)
        self.game.state = State(self.game, num=1)
        self.game.state.check = MagicMock(side_effect=self.game.state.check)
        ret = self.game.process_action(act)
        self.assertTrue(self.game.log['actions'])
        self.assertTrue(self.game.log['messages'])
        self.game.state.check.assert_called_with(self.game)
        self.assertActionResult(ret, 1, 'move', target=loc, unit=d.uid)

    def test_second_movement(self):
        # do a legitimate movement, on a second action
        d = self.unit(2)
        d.chosen_location = Hex(0, 0)
        self.bf.place_object(d)
        loc = Hex(0, 1)
        act = Action(type='move', unit=d, target=loc)
        self.game.state = State(self.game, num=2)
        self.game.state.check = MagicMock(side_effect=self.game.state.check)
        self.game.log['actions'] = [Action(num=2, unit=d, type='pass')]
        ret = self.game.process_action(act)
        self.assertTrue(self.game.log['actions'])
        self.assertTrue(self.game.log['messages'])
        self.game.state.check.assert_called_with(self.game)
        self.assertActionResult(ret, 2, 'move', unit=d.uid, target=loc)

    def test_double_movement(self):
        # cause an Exception by doing two sequential movements
        d = self.unit(2)
        act = Action(type='move', unit=d)
        self.game.state = State(self.game, num=2)
        self.game.log['actions'] = [Action(num=2, unit=d, type='move')]
        self.assertExceptionContains(BattleError,
                                     'Second action in ply must be',
                                     self.game.process_action, act)

    def test_unknown(self):
        # cause an Exception by doing an unknown action
        act = Action(type='xxx')
        self.game.state = State(self.game, num=1)
        self.assertRaises(BattleError, self.game.process_action, act)

    def test_first_attack(self):
        d = self.unit(1)
        a = self.unit(3)
        d.chosen_location = Hex(0, 0)
        a.chosen_location = Hex(0, 1)
        self.bf.place_object(d)
        self.bf.place_object(a)
        wep = Sword(E, create_comp(earth=128))
        d.equip(wep)
        loc = Hex(0, 1)
        act = Action(unit=d, type='attack', target=loc)
        self.game.state = State(self.game, num=1)
        self.game.state.check = MagicMock(side_effect=self.game.state.check)
        ret = self.game.process_action(act)
        self.game.state.check.assert_called_with(self.game)
        self.assertActionResult(ret, 1, type='attack', unit=d.uid, target=loc)

    def test_second_attack(self):
        d = self.unit(2)
        a = self.unit(3)
        d.chosen_location = Hex(0, 0)
        a.chosen_location = Hex(0, 1)
        self.bf.place_object(d)
        self.bf.place_object(a)
        wep = Sword(E, create_comp(earth=128))
        d.equip(wep)
        loc = Hex(0, 1)
        act = Action(unit=d, num=2, type='attack', target=loc)
        self.game.state = State(self.game, num=2)
        self.game.state.check = MagicMock(side_effect=self.game.state.check)
        self.game.log['actions'] = [Action(num=2, unit=d, type='pass')]
        ret = self.game.process_action(act)
        self.game.state.check.assert_called_with(self.game)
        self.assertActionResult(ret, 2, type='attack', unit=d.uid, target=loc)

    def test_double_attack(self):
        d = self.unit(2)
        act = Action(type='attack', unit=d)
        self.game.state = State(self.game, num=2)
        self.game.log['actions'] = [Action(unit=d, num=2, type='attack')]
        self.assertExceptionContains(BattleError,
                                     'Second action in ply must be',
                                     self.game.process_action, act)

    def test_final_action(self):
        self.game.apply_queued = MagicMock(side_effect=self.game.apply_queued)
        self.game.state = State(self.game, num=4)
        self.game.log['actions'] = [Action(num=i + 1, unit=self.unit(i + 1),
                                           type='pass') for i in range(3)]
        act = Action(type='pass', unit=self.unit(4))
        ret = self.game.process_action(act)
        self.game.apply_queued.assert_called_with()
        self.assertActionResult(ret, 4, type='pass', unit=self.unit(4).uid)

    def test_unexpected_unit(self):
        d = self.unit(6)
        act = Action(type='pass', unit=d)
        self.assertExceptionContains(BattleError, 'not the expected unit',
                                     self.game.process_action, act)


class ActionQueueTest(GameTestBase):

    def setUp(self):
        super(ActionQueueTest, self).setUp()

    @property
    def aq(self):
        return self.game.action_queue

    def test_create(self):
        self.assertEqual(self.aq.game, self.game)
        self.assertEqual(len(self.aq.units), 10)

    def test_get_unit_for_action(self):
        # Invalid action num causes exception
        self.assertRaises(ValueError, self.aq.get_unit_for_action, 0)
        # Check various units and their positions in the queue
        # First turn for unit 0
        expect = self.aq.units[0]
        self.assertEqual(self.aq.get_unit_for_action(1), expect)
        self.assertEqual(self.aq.get_unit_for_action(2), expect)
        # First turn, for unit 5
        expect = self.aq.units[5]
        self.assertEqual(self.aq.get_unit_for_action(11), expect)
        self.assertEqual(self.aq.get_unit_for_action(12), expect)
        # Next full turn, for unit 5
        turn = len(self.aq.units) * 2
        self.assertEqual(self.aq.get_unit_for_action(11 + turn), expect)
        self.assertEqual(self.aq.get_unit_for_action(12 + turn), expect)
        # 6 full turns, for unit 5
        self.assertEqual(self.aq.get_unit_for_action(11 + turn * 5), expect)
        self.assertEqual(self.aq.get_unit_for_action(12 + turn * 5), expect)
        # 6 full turns, for unit 6
        expect = self.aq.units[6]
        self.assertEqual(self.aq.get_unit_for_action(13 + turn * 5), expect)
        self.assertEqual(self.aq.get_unit_for_action(14 + turn * 5), expect)

    def assertQueueOrder(self, require_all=False):
        # Verify order by induction
        value_tested = False
        prime_elem_tested = False
        pos_tested = False
        atk_tested = False
        for a, b in pairwise(self.aq.units):
            self.assertNotEqual(a, b)
            # Value <=
            self.assertLessEqual(a.value(), b.value())
            value_tested = True
            if a.value() == b.value():
                # Primary field element value >=
                prime_a = a.comp[self.bf.element]
                prime_b = b.comp[self.bf.element]
                self.assertGreaterEqual(prime_a, prime_b)
                prime_elem_tested = True
                if prime_a == prime_b:
                    # Container pos <=
                    self.assertLessEqual(a.container_pos, b.container_pos)
                    pos_tested = True
                    if a.container_pos == b.container_pos:
                        # Atk before Def
                        self.assertEqual(a.container, self.bf.atksquad)
                        self.assertEqual(b.container, self.bf.defsquad)
                        atk_tested = True
        if require_all:
            # Make sure every condition was reached
            self.assertTrue(value_tested)
            self.assertTrue(prime_elem_tested)
            self.assertTrue(pos_tested)
            self.assertTrue(atk_tested)

    def test_queue_order(self):
        # Test with the random squads
        self.assertQueueOrder()
        # Test with hand-crafted squad intended to catch all cases
        atksquad = Squad()
        defsquad = Squad()
        # Equal value, equal primary element, equal pos, tests atk b4 def
        atksquad.append(Scient(E, create_comp(earth=1)))
        defsquad.append(Scient(E, create_comp(earth=1)))
        # Equal value, equal primary element, different pos, tests pos
        atksquad.append(Scient(F, create_comp(fire=100)))
        atksquad.append(Scient(F, create_comp(fire=100)))
        defsquad.append(Scient(F, create_comp(fire=100)))
        # Equal value, different primary element, tests primary elem
        atksquad.append(Scient(F, create_comp(fire=100)))
        defsquad.append(Scient(E, create_comp(earth=100)))
        # Different value tests value check
        atksquad.append(Scient(E, create_comp(earth=1)))
        defsquad.append(Scient(E, create_comp(earth=2)))
        self._setup_game(atksquad=atksquad, defsquad=defsquad, element=E)
        self.assertQueueOrder(require_all=True)

    def test_get_unit_key_bad_unit(self):
        unit = Scient(E, create_comp(earth=128))
        # neither squad nor squad_pos
        self.assertRaises(ValueError, self.aq._get_unit_key, unit)
        # squad, but no squad_pos
        unit.squad = self.defender.squads[0]
        self.assertRaises(ValueError, self.aq._get_unit_key, unit)
        # squad_pos, but no squad
        unit.squad = None
        unit.squad_pos = 0
        self.assertRaises(ValueError, self.aq._get_unit_key, unit)
        # not in a battling squad
        unit.squad = Squad(data=[unit])
        self.assertRaises(ValueError, self.aq._get_unit_key, unit)
