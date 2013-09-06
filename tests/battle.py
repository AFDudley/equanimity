import itertools
from unittest import TestCase
from mock import MagicMock
from base import create_comp, FlaskTestDB, pairwise
from server.utils import AttributeDict
from equanimity.grid import Grid, Hex
from equanimity.const import E, F
from equanimity.weapons import Sword
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
        s.location = Hex(0, 0)
        log = Log([], {0: s}, Grid())
        locs = log.init_locs()
        self.assertEqual(locs[0], Hex(0, 0))

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
        squad.owner = player
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


class BattleTestBase(FlaskTestDB):
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


class StateTest(BattleTestBase):

    def setUp(self):
        super(StateTest, self).setUp()
        self.s = State()
        self.attacker = Player('Atk', 'x@gmail.com', 'xxx',
                               squads=[rand_squad()])
        defsquad = rand_squad()
        self.defender = Player('Def', 'y@gmail.com', 'xxx', squads=[defsquad])
        self.game = Game(self.attacker, self.defender)
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


class GameTestBase(BattleTestBase):

    def setUp(self):
        super(GameTestBase, self).setUp()
        self._setup_game()

    def _setup_game(self, atksquad=None, defsquad=None, element=None):
        if atksquad is None:
            atksquad = rand_squad(suit=E)
        if defsquad is None:
            defsquad = rand_squad(suit=F)
        self.attacker = Player('Atk', 'x@gmail.com', 'xxx',
                               squads=[atksquad])
        self.defender = Player('Def', 'y@gmail.com', 'yyy',
                               squads=[defsquad])
        self.game = Game(self.attacker, self.defender, element=element)

    @property
    def bf(self):
        return self.game.battlefield

    @property
    def units(self):
        return sorted(list(itertools.chain(self.attacker.squads[0],
                                           self.defender.squads[0])))

    def _place_squads(self):
        self.bf.rand_place_squad(self.attacker.squads[0])
        self.bf.rand_place_squad(self.defender.squads[0])
        self.game.put_squads_on_field()


class GameTest(GameTestBase):

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
        self.bf.dmg_queue[dfdr].append([100, 2])
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
        self.bf.dmg_queue[dfdr].append([1, 2])
        qd = self.bf.apply_queued()
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

    def test_apply_queued(self):
        self._place_squads()
        self._add_actions(4)
        dfdr = self.defender.squads[0][0]
        self.bf.dmg_queue[dfdr].append([1, 2])
        self.game.state.check = MagicMock(side_effect=self.game.state.check)
        self.assertFalse(self.game.log['applied'])
        self.game.apply_queued()
        self.assertTrue(self.game.log['applied'])
        self.game.state.check.assert_called_with(self.game)

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

    def test_end(self):
        self._place_squads()
        self.game.winner = self.defender
        survivors = self.defender.squads[0][:2]
        survivors += self.attacker.squads[0][:1]
        hps = {unit: unit.hp for unit in survivors}
        self.game.state = State(HPs=hps)
        self.game.end('Defender won')
        self.assertGameOver(self.defender, 'Defender won')
        self.assertEqual(sorted(self.defender.squads[0][:2]),
                         sorted(self.game.log['change_list']['victors']))
        self.assertEqual(sorted(self.attacker.squads[0][:1]),
                         sorted(self.game.log['change_list']['prisoners']))


class BattleProcessActionTest(GameTestBase):

    def setUp(self):
        super(BattleProcessActionTest, self).setUp()

    @property
    def d(self):
        return self.defender.squads[0][0]

    @property
    def a(self):
        return self.attacker.squads[0][0]

    def assertActionResult(self, result, num, type, msg=None, target=None,
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
        self.game.state = State(num=1)
        ret = self.game.process_action(act)
        self.assertActionResult(ret, 1, 'pass', 'Action Passed.')

    def test_timing_out(self):
        # same, but timing out
        act = Action(type='timed_out')
        self.game.state = State(num=1)
        ret = self.game.process_action(act)
        self.assertActionResult(ret, 1, 'timed_out', 'Failed to act.')

    def test_using_different_units(self):
        # get a ValueError by using two different units in a row
        act = Action(type='move', unit=self.defender.squads[0][0])
        self.game.state = State(num=2)
        self.game.log['actions'] = [Action(unit=self.defender.squads[0][1])]
        self.assertRaises(ValueError, self.game.process_action, act)

    def test_first_movement(self):
        # do a legitimate movement, on a first action
        self.bf.place_object(self.d, Hex(0, 0))
        loc = Hex(0, 1)
        act = Action(type='move', unit=self.d, target=loc)
        self.game.state = State(num=1)
        self.game.state.check = MagicMock(side_effect=self.game.state.check)
        ret = self.game.process_action(act)
        self.assertTrue(self.game.log['actions'])
        self.assertTrue(self.game.log['messages'])
        self.game.state.check.assert_called_with(self.game)
        self.assertActionResult(ret, 1, 'move', target=loc, unit=6)

    def test_second_movement(self):
        # do a legitimate movement, on a second action
        self.bf.place_object(self.d, Hex(0, 0))
        loc = Hex(0, 1)
        act = Action(type='move', unit=self.d, target=loc)
        self.game.state = State(num=2)
        self.game.state.check = MagicMock(side_effect=self.game.state.check)
        self.game.log['actions'] = [Action(unit=self.d, type='pass')]
        ret = self.game.process_action(act)
        self.assertTrue(self.game.log['actions'])
        self.assertTrue(self.game.log['messages'])
        self.game.state.check.assert_called_with(self.game)
        self.assertActionResult(ret, 2, 'move', unit=self.d.id, target=loc)

    def test_double_movement(self):
        # cause an Exception by doing two sequential movements
        act = Action(type='move', unit=self.d)
        self.game.state = State(num=2)
        self.game.log['actions'] = [Action(unit=self.d, type='move')]
        self.assertRaises(ValueError, self.game.process_action, act)
        try:
            self.game.process_action(act)
        except ValueError as e:
            self.assertIn('Second action in ply must be', str(e))

    def test_unknown(self):
        # cause an Exception by doing an unknown action
        act = Action(type='xxx')
        self.game.state = State(num=1)
        self.assertRaises(ValueError, self.game.process_action, act)

    def test_first_attack(self):
        self.bf.place_object(self.d, Hex(0, 0))
        self.bf.place_object(self.a, Hex(0, 1))
        wep = Sword(E, create_comp(earth=128))
        self.d.equip(wep)
        loc = Hex(0, 1)
        act = Action(unit=self.d, type='attack', target=loc)
        self.game.state = State(num=1)
        self.game.state.check = MagicMock(side_effect=self.game.state.check)
        ret = self.game.process_action(act)
        self.game.state.check.assert_called_with(self.game)
        self.assertActionResult(ret, 1, type='attack', unit=self.d.id,
                                target=loc)

    def test_second_attack(self):
        self.bf.place_object(self.d, Hex(0, 0))
        self.bf.place_object(self.a, Hex(0, 1))
        wep = Sword(E, create_comp(earth=128))
        self.d.equip(wep)
        loc = Hex(0, 1)
        act = Action(unit=self.d, type='attack', target=loc)
        self.game.state = State(num=2)
        self.game.state.check = MagicMock(side_effect=self.game.state.check)
        self.game.log['actions'] = [Action(unit=self.d, type='pass')]
        ret = self.game.process_action(act)
        self.game.state.check.assert_called_with(self.game)
        self.assertActionResult(ret, 2, type='attack', unit=self.d.id,
                                target=loc)

    def test_double_attack(self):
        act = Action(type='attack', unit=self.d)
        self.game.state = State(num=2)
        self.game.log['actions'] = [Action(unit=self.d, type='attack')]
        self.assertRaises(ValueError, self.game.process_action, act)

    def test_final_action(self):
        self.game.apply_queued = MagicMock(side_effect=self.game.apply_queued)
        self.game.state = State(num=4)
        self.game.log['actions'] = [Action(unit=self.d, type='pass')] * 3
        act = Action(type='pass', unit=self.d)
        ret = self.game.process_action(act)
        self.game.apply_queued.assert_called_with()
        self.assertActionResult(ret, 4, type='pass', unit=self.d.id)


class ActionQueueTest(GameTestBase):

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
