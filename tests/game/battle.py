import itertools
from unittest import TestCase
from mock import MagicMock, patch, call, Mock
from operator import attrgetter
from datetime import timedelta, datetime
from ..base import create_comp, FlaskTestDB, FlaskTestDBWorld, pairwise
from equanimity.helpers import AttributeDict
from equanimity.grid import Grid, Hex
from equanimity.const import E, F, I, PLY_TIME
from equanimity.weapons import Sword
from equanimity.units import Scient
from equanimity.field import Field
from equanimity.stone import Stone
from equanimity.player import Player
from equanimity.unit_container import Squad, rand_squad
from equanimity.battle import (now, Action, Message, ChangeList, BattleChanges,
                               InitialState, Log, State, Battle, BattleError)


class ActionTest(TestCase):

    def test_create(self):
        a = Action()
        self.assertGreaterEqual(now(), a.when)
        self.assertTrue(a.target.is_null())
        self.assertEqual(a.type, 'pass')
        self.assertIs(a.unit, None)
        self.assertIs(a.num, None)
        return a


class MessageTest(TestCase):

    def test_create(self):
        m = Message(1, None)
        self.assertEqual(m.num, 1)
        self.assertIs(m.result, None)
        self.assertTrue(m.when)


class ChangeListTest(TestCase):

    def test_create(self):
        c = ChangeList(None, something=1)
        self.assertEqual(c.something, 1)
        self.assertIs(c.event, None)


class BattleChangesTest(TestCase):

    def test_create(self):
        b = BattleChanges([0], [1], [2], event='test')
        self.assertEqual(b.event, 'test')
        self.assertEqual(b.victors, [0])
        self.assertEqual(b.prisoners, [1])
        self.assertEqual(b.awards, [2])


class InitialStateTest(TestCase):

    def test_create(self):
        player = AttributeDict(name='test')
        log = AttributeDict(players=[player], init_locs=1, start_time=now(),
                            units=[2], grid=None, owners=[7, 7])
        i = InitialState(log)
        self.assertEqual(i.player_names, ('test',))
        for k, v in log.iteritems():
            if k != 'players':
                self.assertEqual(getattr(i, k), v)


class BattleModuleTestBase(FlaskTestDBWorld):

    def assertGameOver(self, winner, condition):
        self.assertTrue(self.battle.state.game_over)
        self.assertEqual(self.battle.winner, winner)
        self.assertEqual(self.battle.log.condition, condition)

    def _add_action(self, **action_kwargs):
        self.battle.log.actions.append(Action(**action_kwargs))

    def _add_actions(self, count, **action_kwargs):
        [self._add_action(**action_kwargs) for i in xrange(count)]

    def _check(self):
        self.s.check(self.battle)


class BattleTestBase(BattleModuleTestBase):

    def setUp(self):
        super(BattleTestBase, self).setUp()
        self._setup_battle()

    def _setup_battle(self, atksquad=None, defsquad=None, element=None):
        if atksquad is None:
            atksquad = rand_squad(element=E, size=5)
        if defsquad is None:
            defsquad = rand_squad(element=F, size=5)
        self.attacker = Player('Atk', 'x@gmail.com', 'xxx')
        self.defender = Player('Def', 'y@gmail.com', 'yyy')
        atksquad.owner = self.attacker
        defsquad.owner = self.defender
        f = Field(self.world, (0, 0), I, owner=self.defender)
        self.field = self.world.fields[(0, 0)]
        self.field.owner = self.defender
        self.field.stronghold._add_squad(defsquad)
        self.field.stronghold.defenders = defsquad
        f = self.world.fields[(0, 1)]
        f.owner = self.attacker
        f.stronghold._add_squad(atksquad)
        self.battle = Battle(self.field, atksquad)
        self.commit()

    @property
    def bf(self):
        return self.battle.battlefield

    @property
    def f(self):
        return self.battle.field

    @property
    def units(self):
        return sorted(list(itertools.chain(
            self.defender.get_squads(self.world.uid)[0],
            self.attacker.get_squads(self.world.uid)[0]
        )))

    def _place_squads(self):
        self.f.rand_place_squad(self.attacker.get_squads(self.world.uid)[0])
        self.f.rand_place_squad(self.defender.get_squads(self.world.uid)[0])
        self.battle.start()


class LogTest(FlaskTestDB):

    def test_create(self):
        log = Log([], {}, Grid())
        self.assertTrue(log)
        keys = ['actions', 'applied', 'condition', 'change_list', 'event',
                'end_time', 'init_locs', 'messages', 'owners', 'start_time',
                'states', 'winner', 'world_coords', 'players', 'units', 'grid']
        for k in keys:
            self.assertTrue(hasattr(log, k))

    def test_set_initial_locations(self):
        s = Scient(E, create_comp(earth=128))
        s.owner = Player('testplayer', 't@gmail.com', 'xxx')
        s.location = Hex(0, 0)
        log = Log([], {s: s.uid}, Grid())
        log.set_initial_locations()
        self.assertEqual(log.init_locs[s.uid], Hex(0, 0))

    def test_close(self):
        log = Log([], {}, Grid())
        log.close('you', 'done')
        self.assertEqual(log.winner, 'you')
        self.assertEqual(log.condition, 'done')
        self.assertGreaterEqual(now(), log.end_time)

    def test_get_owners(self):
        s = Scient(E, create_comp(earth=128))
        player = Player('testplayer', 't@gmail.com', 'xxx')
        Squad(name='test', data=[s], owner=player)
        log = Log([player], {s: s.uid}, Grid())
        owners = log.get_owners()
        self.assertEqual(owners, {s.uid: 'testplayer'})

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


class LogTestAdvanced(BattleTestBase):

    def test_last_message(self):
        self._place_squads()
        none = ['There was no message.']
        # No messages in log, at all
        self.assertEqual(self.battle.log.last_message(), none)
        # No result in last message
        self.battle.log.messages.append(AttributeDict(result=None))
        self.assertEqual(self.battle.log.last_message(), none)
        # A result in last message
        res = ['A message']
        self.battle.log.messages.append(AttributeDict(result=res))
        self.assertEqual(self.battle.log.last_message(), res)


class StateTest(BattleModuleTestBase):

    def setUp(self):
        super(StateTest, self).setUp()
        self.attacker = Player('Atk', 'x@gmail.com', 'xxx')
        atksquad = rand_squad()
        atksquad.owner = self.attacker
        self.defender = Player('Def', 'y@gmail.com', 'xxx')
        defsquad = rand_squad()
        defsquad.owner = self.defender
        self.field = self.world.fields[(0, 0)]
        self.field.owner = self.defender
        self.field.stronghold._add_squad(defsquad)
        f = self.world.fields[(0, 1)]
        f.owner = self.attacker
        f.stronghold._add_squad(atksquad)
        self.battle = Battle(self.field, atksquad)
        self.s = State(self.battle)
        self.s.old_defsquad_hp = defsquad.hp()

    def test_create(self):
        keys = ['hps', 'queued', 'locs', 'num', 'pass_count', 'hp_count',
                'old_defsquad_hp', 'game_over', 'whose_action']
        for k in keys:
            self.assertTrue(hasattr(self.s, k))

    def test_check_single_action(self):
        self._add_action()
        self._check()
        self.assertEqual(self.s.pass_count, 1)

    def test_check_nonpass_action(self):
        self._add_action(type='move')
        self._check()
        self.assertEqual(self.s.pass_count, 0)

    def test_complete_turn_no_defender_damage(self):
        self.s.num = 4
        self.s.old_defsquad_hp = self.battle.battlefield.defsquad.hp() - 1
        self._add_actions(4)
        self._check()
        self.assertEqual(self.s.hp_count, 0)

    def test_complete_turn_defender_took_damage(self):
        self.battle.battlefield.defsquad[0].hp = 0
        self._add_actions(4)
        self.s.num = 4
        self._check()
        self.assertEqual(self.s.hp_count, 1)

    def test_game_over_not_enough_damage(self):
        # test for game over check, where attacker was not able to kill
        self._add_actions(4)
        for i in xrange(4):
            self.s.num = 4
            self.s.old_defsquad_hp *= 2
            self._check()
        self.assertEqual(self.s.hp_count, 4)
        self.assertGameOver(self.defender,
                            'Attacker failed to deal sufficent damage.')

    def test_game_over_defenders_killed(self):
        # test for game over check, where defending squad is dead
        self._add_action()
        for squad in self.defender.get_squads(self.world.uid):
            for unit in squad:
                unit.hp = 0
        self.s.old_defsquad_hp = 0
        self._check()
        self.assertGameOver(self.attacker, 'Defender\'s squad is dead')

    def test_game_over_attackers_killed(self):
        # test for game over check, where attacking squad is dead
        self._add_action()
        for squad in self.attacker.get_squads(self.world.uid):
            for unit in squad:
                unit.hp = 0
        self.s.old_defsquad_hp = 0
        self._check()
        self.assertGameOver(self.defender, 'Attacker\'s squad is dead')

    def test_game_over_everyone_passed(self):
        # test for game over, where both sides passed
        self._add_actions(8)
        for i in xrange(8):
            self.s.num = i + 1
            self._check()
        self.assertGameOver(self.defender, 'Both sides passed')


class GameTest(BattleTestBase):

    def setUp(self):
        super(GameTest, self).setUp()

    def test_create(self):
        self.assertEqual(self.battle.attacker, self.attacker)
        self.assertEqual(self.battle.defender, self.defender)
        self.assertEqual(sorted(set(self.battle.log.owners.values())),
                         sorted(['Atk', 'Def']))

    def test_put_squads_on_field(self):
        self._place_squads()
        self.assertTrue(self.battle.log.init_locs)
        for unit in self.units:
            self.assertIsNot(unit.location, None)
            self.assertNotEqual(unit.location, Hex.null)

    def test_map_locs(self):
        self._place_squads()
        locs = self.battle.map_locs()
        self.assertEqual(
            sorted(locs.keys()), sorted(self.battle.units.values()))
        self.assertEqual(sorted(locs.values()),
                         sorted([u.location for u in self.units]))

    def test_hps(self):
        self._place_squads()
        hps = self.battle.hps()
        self.assertEqual(
            sorted(hps.keys()), sorted(self.battle.units.values()))
        self.assertEqual(sorted(hps.values()),
                         sorted([u.hp for u in self.units]))

    def test_update_unit_info(self):
        self._place_squads()
        hps, locs = self.battle.update_unit_info()
        self.assertEqual(hps, self.battle.hps())
        self.assertEqual(locs, self.battle.map_locs())

    def test_map_queue(self):
        self._place_squads()
        dfdr = self.defender.get_squads(self.world.uid)[0][0]
        self.bf.dmg_queue[dfdr].append([100, 2])
        dmg_q = self.battle.map_queue()
        self.assertTrue(dmg_q)
        self.assertIn(dfdr.uid, dmg_q)
        for uid, dmg in dmg_q.iteritems():
            if uid == dfdr.uid:
                self.assertEqual(dmg, [[100, 2]])
            else:
                self.assertEqual(dmg, [])

    def test_map_result(self):
        self._place_squads()
        dfdr = self.defender.get_squads(self.world.uid)[0][0]
        self.bf.dmg_queue[dfdr].append([1, 2])
        qd = self.bf.apply_queued()
        self.assertEqual(self.battle.map_result(qd), [[dfdr.uid, 1]])

    def test_map_action(self):
        d = self.defender.get_squads(self.world.uid)[0][0]
        act = self.battle.map_action(Action(unit=d))
        self.assertEqual(act.unit, d.uid)

    def test_apply_queued(self):
        self._place_squads()
        self._add_actions(4)
        dfdr = self.defender.get_squads(self.world.uid)[0][0]
        self.bf.dmg_queue[dfdr].append([1, 2])
        self.assertFalse(self.battle.log.applied)
        self.battle.apply_queued()
        self.assertTrue(self.battle.log.applied)

    def test_initial_state(self):
        init_state = self.battle.initial_state()
        self.assertTrue(isinstance(init_state, InitialState))

    def test_compute_award(self):
        self.defender.get_squads(self.world.uid)[0][0].hp = 0
        comp = self.defender.get_squads(self.world.uid)[0][0].copy()
        wep_comp = Stone(create_comp(earth=2))
        weapon = Sword(E, wep_comp)
        wep_comp = wep_comp.copy().extract_award()
        self.defender.get_squads(self.world.uid)[0][0].equip(weapon)
        awards = self.battle.compute_awards(self.battle.battlefield.squads)
        comp = comp.extract_award()
        self.assertEqual(awards, [comp, wep_comp])

    def test_clean_up_dead_units(self):
        # Set some hps to <= 0, and check that are removed from the stronghold
        self.battle.battlefield.squads[:]
        defsquad = self.defender.get_squads(self.world.uid)[0]
        atksquad = self.attacker.get_squads(self.world.uid)[0]
        self.assertEqual(defsquad,
                         defsquad.stronghold.squads[defsquad.stronghold_pos])
        self.assertEqual(atksquad,
                         atksquad.stronghold.squads[atksquad.stronghold_pos])
        defsquad[0].hp = 0
        atksquad[0].hp = -1
        defsquadlen = len(defsquad)
        atksquadlen = len(atksquad)
        strongholdlen = len(defsquad.stronghold.squads)
        defstronghold = defsquad.stronghold
        defstronghold_pos = defsquad.stronghold_pos
        self.battle.clean_up_dead_units(self.battle.battlefield.squads)
        self.assertEqual(len(defsquad), defsquadlen - 1)
        self.assertEqual(len(atksquad), atksquadlen - 1)
        self.assertEqual(defsquad,
                         defsquad.stronghold.squads[defsquad.stronghold_pos])
        self.assertEqual(atksquad,
                         atksquad.stronghold.squads[atksquad.stronghold_pos])
        # Now, set all hps in one squad to <= 0, and check that the squad is
        # removed from the stronghold entirely
        self.assertNotEqual(len(defsquad), 0)
        for u in defsquad:
            u.hp = 0
        self.assertEqual(defsquad, self.battle.battlefield.defsquad)
        self.assertIn(defsquad, self.battle.battlefield.squads)
        self.assertFalse(filter(lambda x: x.hp > 0, defsquad))
        self.battle.clean_up_dead_units(self.battle.battlefield.squads)
        self.assertIsNone(defsquad.stronghold)
        self.assertIsNone(defsquad.stronghold_pos)
        self.assertEqual(strongholdlen - 1, len(defstronghold.squads))
        self.assertIsNone(
            defstronghold.squads.get(defstronghold_pos))

    def test_get_victors_and_prisoners(self):
        self.battle.winner = self.attacker
        v, p = self.battle.get_victors_and_prisoners()
        self.assertEqual(list(v), list(self.battle.battlefield.atksquad))
        self.assertEqual(list(p), list(self.battle.battlefield.defsquad))
        self.battle.winner = self.defender
        v, p = self.battle.get_victors_and_prisoners()
        self.assertEqual(list(v), list(self.battle.battlefield.defsquad))
        self.assertEqual(list(p), list(self.battle.battlefield.atksquad))

    @patch('equanimity.battle.Battle.clean_up_dead_units')
    @patch('equanimity.silo.Silo.imbue_list')
    @patch('equanimity.field.Field.get_taken_over')
    @patch('equanimity.stronghold.Stronghold.add_free_unit')
    @patch('equanimity.field.Field.check_ungarrisoned')
    def test_update_field_attacker_wins(self, mock_garr, mock_add, mock_taken,
                                        mock_imbue, mock_clean):
        # Update with attacker wins
        self.battle.winner = self.attacker
        atksquad = self.battle.battlefield.atksquad
        defsquad = self.battle.battlefield.defsquad
        prisoners = [u for u in defsquad]
        awards = [Stone(create_comp(earth=2, ice=3, fire=1, wind=7))]
        self.battle.update_field(atksquad, defsquad, awards, prisoners)
        mock_garr.assert_called_once_with()
        mock_add.assert_not_called()
        mock_clean.assert_called_once_with([atksquad, defsquad])
        mock_taken.assert_called_once_with(atksquad)
        mock_imbue.assert_called_once_with(awards)

    @patch('equanimity.battle.Battle.clean_up_dead_units')
    @patch('equanimity.silo.Silo.imbue_list')
    @patch('equanimity.field.Field.get_taken_over')
    @patch('equanimity.stronghold.Stronghold.add_free_unit')
    @patch('equanimity.field.Field.check_ungarrisoned')
    def test_update_field_defender_wins(self, mock_garr, mock_add, mock_taken,
                                        mock_imbue, mock_clean):
        # Update with defender wins
        self.battle.winner = self.defender
        atksquad = self.battle.battlefield.atksquad
        defsquad = self.battle.battlefield.defsquad
        prisoners = [u for u in atksquad]
        awards = [Stone(create_comp(earth=2, ice=3, fire=1, wind=7))]
        self.battle.update_field(atksquad, defsquad, awards, prisoners)
        mock_garr.assert_called_once_with()
        prisoners = sorted(prisoners, key=attrgetter('value'),
                           reverse=True)
        mock_add.assert_has_calls([call(u) for u in prisoners])
        mock_clean.assert_called_once_with([atksquad, defsquad])
        mock_taken.assert_not_called()
        mock_imbue.assert_called_once_with(awards)

    @patch('equanimity.battle.Battle.clean_up_dead_units')
    @patch('equanimity.silo.Silo.imbue_list')
    @patch('equanimity.field.Field.get_taken_over')
    @patch('equanimity.stronghold.Stronghold.add_free_unit')
    @patch('equanimity.field.Field.check_ungarrisoned')
    def test_update_field_defender_wins_stronghold_full(
            self, mock_garr, mock_add, mock_taken, mock_imbue, mock_clean):
        # Update with defender wins
        mock_add.side_effect = ValueError
        self.battle.winner = self.defender
        atksquad = self.battle.battlefield.atksquad
        defsquad = self.battle.battlefield.defsquad
        prisoners = [u for u in atksquad]
        awards = [Stone(create_comp(earth=2, ice=3, fire=1, wind=7))]
        self.battle.update_field(atksquad, defsquad, awards, prisoners)
        mock_garr.assert_called_once_with()
        prisoner = None
        for p in prisoners:
            if prisoner is None or p.value > prisoner.value:
                prisoner = p
        self.assertIsNotNone(prisoner)
        mock_add.assert_called_once_with(prisoner)
        mock_clean.assert_called_once_with([atksquad, defsquad])
        mock_taken.assert_not_called()
        mock_imbue.assert_called_once_with(awards)

    @patch('equanimity.silo.Silo.imbue_list')
    @patch.object(Battle, 'compute_awards')
    def test_end(self, mock_compute_awards, mock_imbue):
        awards = [Stone(create_comp(earth=2, ice=3, fire=1, wind=7))]
        mock_compute_awards.return_value = awards
        self._place_squads()
        self.battle.winner = self.defender
        defsquad = self.defender.get_squads(self.world.uid)[0]
        for u in defsquad[2:]:
            u.hp = 0
        atksquad = self.attacker.get_squads(self.world.uid)[0]
        for u in atksquad[1:]:
            u.hp = -1
        def_survivors = defsquad[:2]
        atk_survivors = atksquad[:1]
        self.battle.end('Defender won')
        self.assertGameOver(self.defender, 'Defender won')
        for u in self.battle.log.change_list.victors:
            self.assertGreater(u.hp, 0)
        for u in self.battle.log.change_list.prisoners:
            self.assertGreater(u.hp, 0)
        self.assertEqual(sorted(def_survivors),
                         sorted(self.battle.log.change_list.victors))
        self.assertEqual(sorted(atk_survivors),
                         sorted(self.battle.log.change_list.prisoners))
        mock_compute_awards.assert_called_once_with(
            self.battle.battlefield.squads)
        mock_imbue.assert_called_once_with(awards)


class BattleProcessActionTest(BattleTestBase):

    def setUp(self):
        super(BattleProcessActionTest, self).setUp()

    @property
    def d(self):
        return self.defender.get_squads(self.world.uid)[0][0]

    @property
    def a(self):
        return self.attacker.get_squads(self.world.uid)[0][0]

    @property
    def past(self):
        return datetime.utcnow() - PLY_TIME - timedelta(minutes=5)

    def unit(self, num):
        return self.battle.action_queue.get_unit_for_action(num)

    def assertActionResult(self, result, num, type, msg=None, target=Hex.null,
                           unit=None):
        if num % 4:
            self.assertIsNone(result.applied)
        else:
            self.assertIsNotNone(result.applied)
        self.assertEqual(result.command.num, num)
        self.assertEqual(result.command.type, type)
        self.assertEqual(result.command.target, target)
        self.assertEqual(result.command.unit, unit)
        self.assertEqual(result.response.num, num)
        if msg is not None:
            self.assertEqual(result.response.result, [[msg]])

    def test_doing_nothing(self):
        # with no unit, no prev_unit, no prev_act, passing
        act = Action()
        self.battle.state = State(self.battle, num=1)
        ret = self.battle.process_action(act)
        self.assertActionResult(ret, 1, 'pass', 'Action Passed.')

    def test_timeout_first_action_start_time(self):
        self.battle.log.start_time = self.past
        act = Action(type='move', num=1, unit=self.unit(1))
        self.battle.state = State(self.battle, num=1)
        ret = self.battle._process_action(act)
        self.assertActionResult(ret, 1, 'timed_out', 'Failed to act.',
                                unit=self.unit(1).uid)

    def test_timeout_second_action_start_time(self):
        self.battle.log.start_time = self.past
        act = Action(type='move', unit=self.unit(2))
        self.battle.state = State(self.battle, num=2)
        self.battle.log.actions = [Action(num=1, unit=self.unit(1))]
        ret = self.battle._process_action(act)
        self.assertActionResult(ret, 2, 'timed_out', 'Failed to act.',
                                unit=self.unit(2).uid)

    def test_timeout_first_action_after_other_action(self):
        act = Action(type='move', unit=self.unit(3))
        self.battle.state = State(self.battle, num=3)
        self.battle.log.actions = [Action(unit=self.unit(1), when=self.past),
                                   Action(unit=self.unit(2), when=self.past)]
        ret = self.battle._process_action(act)
        self.assertActionResult(ret, 3, 'timed_out', 'Failed to act.',
                                unit=self.unit(3).uid)

    def test_timeout_second_action_after_other_action(self):
        act = Action(type='move', num=4, unit=self.unit(4))
        self.battle.state = State(self.battle, num=4)
        self.battle.log.actions = [Action(unit=self.unit(1), num=1,
                                          when=self.past),
                                   Action(unit=self.unit(2), num=2,
                                          when=self.past),
                                   Action(unit=self.unit(3), num=3)]
        ret = self.battle._process_action(act)
        self.assertActionResult(ret, 4, 'timed_out', 'Failed to act.',
                                unit=self.unit(4).uid)

    def test_timed_out_action(self):
        act = Action(type='timed_out')
        self.battle.state = State(self.battle, num=1)
        ret = self.battle.process_action(act)
        self.assertActionResult(ret, 1, 'timed_out', 'Failed to act.')

    def test_fill_timed_out_actions(self):
        start = self.battle.log.start_time
        self.battle.log.start_time = start - PLY_TIME * 3 - PLY_TIME / 2
        self.battle._fill_timed_out_actions()
        actions = self.battle.log.actions
        n = 6
        self.assertEqual(self.battle.state.num, n + 1)
        self.assertEqual(len(actions), n)
        # All numbers should be in sequence
        for n, act in enumerate(actions):
            self.assertEqual(n + 1, act.num)
            # same ply whens should be equal
            if n % 2:
                self.assertEqual(act.when, actions[n - 1].when)
        # All times should be ascending
        for i in reversed(range(1, n)):
            self.assertGreaterEqual(actions[i].when,
                                    actions[i - 1].when)
        # All times should definitely be greater across plies
        for i in reversed(range(3, n, 2)):
            self.assertGreater(actions[i].when, actions[i - 2].when)
        # Processing an action should work as expected
        act = Action(type='pass', unit=self.unit(7))
        ret = self.battle.process_action(act)
        self.assertActionResult(ret, 7, 'pass', 'Action Passed.',
                                unit=self.unit(7).uid)

    def test_using_different_units(self):
        # get a ValueError by using two different units in a row
        act = Action(type='move', num=2, unit=self.unit(2))
        self.battle.state = State(self.battle, num=2)
        self.battle.log.actions = [Action(num=4, unit=self.unit(4))]
        self.assertExceptionContains(BattleError,
                                     'Unit from the previous action',
                                     self.battle.process_action, act)

    def test_first_movement(self):
        # do a legitimate movement, on a first action
        d = self.unit(1)
        d.chosen_location = Hex(0, 0)
        self.bf.place_object(d)
        loc = Hex(0, 1)
        act = Action(type='move', unit=d, target=loc)
        self.battle.state = State(self.battle, num=1)
        self.battle.state.check = MagicMock(
            side_effect=self.battle.state.check)
        ret = self.battle.process_action(act)
        self.assertTrue(self.battle.log.actions)
        self.assertTrue(self.battle.log.messages)
        self.battle.state.check.assert_called_with(self.battle)
        self.assertActionResult(ret, 1, 'move', target=loc, unit=d.uid)

    def test_second_movement(self):
        # do a legitimate movement, on a second action
        d = self.unit(2)
        d.chosen_location = Hex(0, 0)
        self.bf.place_object(d)
        loc = Hex(0, 1)
        act = Action(type='move', unit=d, target=loc)
        self.battle.state = State(self.battle, num=2)
        self.battle.state.check = MagicMock(
            side_effect=self.battle.state.check)
        self.battle.log.actions = [Action(num=2, unit=d, type='pass')]
        ret = self.battle.process_action(act)
        self.assertTrue(self.battle.log.actions)
        self.assertTrue(self.battle.log.messages)
        self.battle.state.check.assert_called_with(self.battle)
        self.assertActionResult(ret, 2, 'move', unit=d.uid, target=loc)

    def test_double_movement(self):
        # cause an Exception by doing two sequential movements
        d = self.unit(2)
        act = Action(type='move', unit=d)
        self.battle.state = State(self.battle, num=2)
        self.battle.log.actions = [Action(num=2, unit=d, type='move')]
        self.assertExceptionContains(BattleError,
                                     'Second action in ply must be',
                                     self.battle.process_action, act)

    def test_unknown(self):
        # cause an Exception by doing an unknown action
        act = Action(type='xxx')
        self.battle.state = State(self.battle, num=1)
        self.assertRaises(BattleError, self.battle.process_action, act)

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
        self.battle.state = State(self.battle, num=1)
        self.battle.state.check = MagicMock(
            side_effect=self.battle.state.check)
        ret = self.battle.process_action(act)
        self.battle.state.check.assert_called_with(self.battle)
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
        self.battle.state = State(self.battle, num=2)
        self.battle.state.check = MagicMock(
            side_effect=self.battle.state.check)
        self.battle.log.actions = [Action(num=2, unit=d, type='pass')]
        ret = self.battle.process_action(act)
        self.battle.state.check.assert_called_with(self.battle)
        self.assertActionResult(ret, 2, type='attack', unit=d.uid, target=loc)

    def test_double_attack(self):
        d = self.unit(2)
        act = Action(type='attack', unit=d)
        self.battle.state = State(self.battle, num=2)
        self.battle.log.actions = [Action(unit=d, num=2, type='attack')]
        self.assertExceptionContains(BattleError,
                                     'Second action in ply must be',
                                     self.battle.process_action, act)

    def test_final_action(self):
        self.battle.apply_queued = MagicMock(
            side_effect=self.battle.apply_queued)
        self.battle.state = State(self.battle, num=4)
        self.battle.log.actions = [Action(num=i + 1, unit=self.unit(i + 1),
                                          type='pass') for i in range(3)]
        act = Action(type='pass', unit=self.unit(4))
        ret = self.battle.process_action(act)
        self.battle.apply_queued.assert_called_with()
        self.assertActionResult(ret, 4, type='pass', unit=self.unit(4).uid)

    def test_unexpected_unit(self):
        d = self.unit(6)
        act = Action(type='pass', unit=d)
        self.assertExceptionContains(BattleError, 'not the expected unit',
                                     self.battle.process_action, act)


class ActionQueueTest(BattleTestBase):

    def setUp(self):
        super(ActionQueueTest, self).setUp()

    @property
    def aq(self):
        return self.battle.action_queue

    def test_create(self):
        self.assertEqual(self.aq.battle, self.battle)
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
            self.assertLessEqual(a.value, b.value)
            value_tested = True
            if a.value == b.value:
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

    @patch('equanimity.stronghold.Stronghold.max_occupancy')
    def test_queue_order(self, mock_max):
        mock_max.__get__ = Mock(return_value=128)
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
        self._setup_battle(atksquad=atksquad, defsquad=defsquad, element=E)
        self.assertQueueOrder(require_all=True)

    def test_get_unit_key_bad_unit(self):
        unit = Scient(E, create_comp(earth=128))
        # neither squad nor squad_pos
        self.assertRaises(ValueError, self.aq._get_unit_key, unit)
        # squad, but no squad_pos
        unit.squad = self.defender.get_squads(self.world.uid)[0]
        self.assertRaises(ValueError, self.aq._get_unit_key, unit)
        # squad_pos, but no squad
        unit.squad = None
        unit.squad_pos = 0
        self.assertRaises(ValueError, self.aq._get_unit_key, unit)
        # not in a battling squad
        unit.squad = Squad(data=[unit])
        self.assertRaises(ValueError, self.aq._get_unit_key, unit)
