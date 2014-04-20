"""
battle.py

Created by AFD on 2013-08-05.
Copyright (c) 2013 A. Frederick Dudley. All rights reserved.
"""
"""
This needs to be refactored to properly generate json/serialized output
and should be refactored with battle as well.

"""
from bidict import bidict, inverted
from datetime import timedelta
from persistent import Persistent
from persistent.list import PersistentList
from persistent.mapping import PersistentMapping
from operator import attrgetter
from functools import partial

from server import db
from battlefield import Battlefield
from units import Unit
from grid import Hex
from const import PLY_TIME
from helpers import now, timestamp, PersistentKwargs
from worldtools import get_world


class BattleError(Exception):
    pass


class Action(PersistentKwargs):

    """In a two player battle, two actions from a single player make a ply and
       a ply from each player makes a turn. """

    def __init__(self, unit=None, type='pass', target=Hex.null, when=None,
                 num=None):
        if when is None:
            when = now()
        super(Action, self).__init__(unit=unit, type=type, target=target,
                                     num=num, when=when)

    def api_view(self):
        return dict(
            unit=self.unit,
            type=self.type,
            target=self.target,
            num=self.num,
            when=self.when,
        )


class Message(PersistentKwargs):

    def __init__(self, num, result):
        super(Message, self).__init__(num=num, result=result, when=now())

    def api_view(self):
        return dict(
            num=self.num,
            result=self.result,
            when=self.when,
        )


class ChangeList(PersistentKwargs):
    # TODO - belongs in different file

    def __init__(self, event, **kwargs):
        super(ChangeList, self).__init__(event=event, **kwargs)


class BattleChanges(ChangeList):

    def __init__(self, victors, prisoners, dead_attackers, dead_defenders,
                 awards, event='battle'):
        super(BattleChanges, self).__init__(event=event, victors=victors,
                                            prisoners=prisoners,
                                            dead_attackers=dead_attackers,
                                            dead_defenders=dead_defenders,
                                            awards=awards)


class ActionResult(PersistentKwargs):

    def __init__(self, command, response, applied=None):
        super(ActionResult, self).__init__(command=command, response=response,
                                           applied=applied)

    def api_view(self):
        return dict(
            command=self.command.api_view(),
            response=self.response.api_view(),
            applied=getattr(self.applied, 'api_view', lambda: None)(),
        )


class InitialState(PersistentKwargs):

    """A hack for serialization."""

    def __init__(self, log):
        names = tuple(player.name for player in log.players)
        super(InitialState, self).__init__(
            init_locs=log.init_locs, start_time=log.start_time,
            units=log.units, grid=log.grid, owners=log.owners,
            player_names=names)

class Log(PersistentKwargs):

    def __init__(self, players, units, grid):
        """Records initial battle state, timestamps log."""
        super(Log, self).__init__(players=players, units=units, grid=grid)
        self.actions = PersistentList()
        self.applied = PersistentList()
        self.condition = None
        self.change_list = None
        self.event = 'battle'
        self.end_time = None
        self.init_locs = None
        self.messages = PersistentList()
        self.start_time = now()
        self.owners = None
        self.states = PersistentList()  # Does this really need to be here?
        self.winner = None
        self.world_coords = None  # set by battle_server
        self.owners = self.get_owners()


    
    def set_initial_locations(self):
        locs = {unit.uid: unit.location for unit in self.units}
        self.init_locs = PersistentMapping(dict=locs)

    def close(self, winner, condition):
        """Writes final timestamp, called when battle is over."""
        self.end_time = now()
        self.winner = winner
        self.condition = condition

    def get_owners(self):
        """Mapping of unit number to player/owner."""
        owners = {unit.uid: unit.owner.name for unit in self.units}
        return PersistentMapping(dict=owners)

    def last_message(self):
        none = ['There was no message.']
        if not self.messages:
            return none
        text = self.messages[-1].result
        if text is None:
            return none
        return text

    def get_time_remaining_for_action(self):
        then = self.get_last_terminating_action_time()
        remaining = now() - then
        if remaining > PLY_TIME:
            remaining = timedelta(seconds=0)
        return remaining

    def get_last_terminating_action(self, current_num=None):
        # Returns the last recorded action that was the final one in a ply
        # Don't provide a current num to retrieve the last tip
        if current_num is None:
            try:
                act = self.actions[-1]
            except IndexError:
                return
            else:
                if act.num % 2:
                    term_action = -2
                else:
                    term_action = -1
        elif current_num % 2:
            term_action = -1
        else:
            term_action = -2
        try:
            return self.actions[term_action]
        except IndexError:
            return

    def get_last_terminating_action_time(self, current_num=None):
        act = self.get_last_terminating_action(current_num=current_num)
        if act is None:
            return self.start_time
        else:
            return act.when

    def action_timed_out(self, action):
        start = self.get_last_terminating_action_time(action.num)
        return (action.when - start > PLY_TIME)


class State(PersistentKwargs):

    """A dictionary containing the current battle state."""

    def __init__(self, battle, num=1, pass_count=0, hp_count=0,
                 old_defsquad_hp=0, queued=None, locs=None, hps=None,
                 game_over=False):
        self.battle = battle
        if hps is None:
            hps = PersistentMapping()
        if queued is None:
            queued = PersistentMapping()
        if locs is None:
            locs = PersistentMapping()
        whose_action = ActionQueue.get_player_for_action(
            self.battle.battlefield, num).uid
        super(State, self).__init__(num=num, pass_count=pass_count,
                                    hp_count=hp_count, queued=queued,
                                    old_defsquad_hp=old_defsquad_hp,
                                    locs=locs, hps=hps, game_over=game_over,
                                    whose_action=whose_action)

    def _kwargs(self):
        """ Returns the kwargs needed to reinitialize State from self """
        return dict(
            num=self.num,
            pass_count=self.pass_count,
            hp_count=self.hp_count,
            old_defsquad_hp=self.old_defsquad_hp,
            queued=self.queued,
            locs=self.locs,
            hps=self.hps,
            game_over=self.game_over,
        )

    def api_view(self):
        return dict(
            battle=self.battle.uid,
            num=self.num,
            pass_count=self.pass_count,
            hp_count=self.hp_count,
            old_defsquad_hp=self.old_defsquad_hp,
            queued=str(self.queued),
            locs=str(self.locs),
            hps=str(self.hps),
            game_over=self.game_over,
            
        )
    
    def snapshot(self, battle):
        """ Creates a copy of self and battle and returns as a new state """
        # TODO -- need to copy battle and all of its descendants?
        s = State(battle, **self._kwargs())
        return s

    def check(self, battle):
        """Checks for battle ending conditions.
        (Assumes two players and no ActionQueue.)"""
        num = self.num
        last_type = battle.log.actions[num - 1].type
        if last_type == 'pass' or last_type == 'timed_out':
            self.pass_count += 1
        else:
            self.pass_count = 0

        if not num % 4:  # There are 4 actions in a turn.
            # This calcuates hp_count
            defsquad_hp = battle.battlefield.defsquad.hp()
            if self.old_defsquad_hp >= defsquad_hp:
                self.hp_count += 1
            else:
                self.hp_count = 0

            # battle over check:
            if self.hp_count == 4:
                battle.winner = battle.defender
                return battle.end("Attacker failed to deal sufficent damage.")
            else:
                self.old_defsquad_hp = defsquad_hp

        # check if battle is over.
        if battle.battlefield.defsquad.hp() == 0:
            battle.winner = battle.attacker
            return battle.end("Defender's squad is dead")

        if battle.battlefield.atksquad.hp() == 0:
            battle.winner = battle.defender
            return battle.end("Attacker's squad is dead")

        if self.pass_count >= 8:
            battle.winner = battle.defender
            return battle.end("Both sides passed")

        self.queued = battle.map_queue()
        self.hps, self.locs = battle.update_unit_info()

        new_state = self.snapshot(battle)
        battle.log.states.append(new_state)

        # battle is not over, state is stored, update state.
        self.num += 1
        aq = ActionQueue
        self.whose_action = aq.get_player_for_action(self.battle.battlefield,
                                                     self.num).uid


class Battle(Persistent):

    """Almost-state-machine that maintains battle state."""

    def __init__(self, field, attacker):
        super(Battle, self).__init__()
        self.defender = field.stronghold.defenders.owner
        self.attacker = attacker.owner
        self.battlefield = Battlefield(field.grid, field.element,
                                       field.stronghold.defenders, attacker)
        units = {unit.uid: unit for unit in self.battlefield.units}
        self.map = bidict(units)
        self.units = bidict(inverted(self.map))
        self.winner = None
        self.log = Log(self.players, self.units, field.grid)
        self.state = State(self)
        self.state.old_defsquad_hp = self.battlefield.defsquad.hp()
        self.field = field
        self.uid = db['battle_uid'].get_next_id()

    def persist(self):
        db['battles'][self.uid] = self

    @classmethod
    def get(self, world, field_loc):
        world = get_world(world)
        if world is not None:
            field = world.fields.get(tuple(field_loc))
            if field is not None:
                return field.battle

    @classmethod
    def get_by_uid(self, id):
        return db['battles'].get(id)

    @property
    def players(self):
        return self.defender, self.attacker

    def start(self):
        self.battlefield.put_squads_on_field()
        self.log.set_initial_locations()

    def timer_view(self):
        num = self.state.num
        remaining = self.get_time_remaining_for_action()
        current_unit = ActionQueue.get_unit_for_action(self.battlefield,
                                                       num)
        return dict(start_time=timestamp(self.log.start_time),
                    action_num=self.state.num,
                    current_ply=ActionQueue.get_action_in_ply(num),
                    current_unit=current_unit.uid,
                    time_remaining=remaining.seconds)

    def states_view(self):
        return [s.api_view() for s in self.log.states]
    
    def messages_view(self):
        return [m.api_view() for m in self.log.messages]
    
    def actions_view(self):
        return [a.api_view() for a in self.log.actions]
    
    def api_view(self):
        return dict(
            uid=self.uid,
            timer=self.timer_view(),
            defender=self.defender.combatant_view(self.battlefield.defsquad),
            attacker=self.attacker.combatant_view(self.battlefield.atksquad),
            action_num=self.state.num,
            game_over=self.state.game_over,
            condition=self.log.condition,
            winner=getattr(self.winner, 'api_view', lambda: None)())

    def map_locs(self):
        """maps unit name unto locations, only returns live units"""
        locs = PersistentMapping()
        for unit in self.units:
            loc = unit.location
            if not loc.is_null():
                locs[unit.uid] = loc
        return locs

    def hps(self):
        """Hit points by unit."""
        hps = {unit.uid: unit.hp for unit in self.units if unit.hp > 0}
        return PersistentMapping(dict=hps)

    def update_unit_info(self):
        """returns hps, Locs."""
        hps = PersistentMapping()
        locs = PersistentMapping()
        for unit in self.units:
            loc = unit.location
            # TODO (steve) -- should we also check hp > 0 ?
            if not loc.is_null():
                locs[unit.uid] = loc
                hps[unit.uid] = unit.hp
        return hps, locs

    def map_queue(self):
        """apply unit mapping to units in queue."""
        queue = self.battlefield.get_dmg_queue()
        return {key.uid: val for key, val in queue.iteritems()}

    def map_result(self, result):
        """ replaces unit references with their hash
        TODO (steve) -- this may be unnecessary and cause problems """
        for t in result:
            if isinstance(t[0], Unit):
                t[0] = t[0].uid
        return result

    def map_action(self, action):
        """replaces unit refrences to referencing their hash.
        TODO (steve) -- this may be unnecessary and cause problems """
        if action.unit is not None:
            action.unit = action.unit.uid
        return action

    def get_time_remaining_for_action(self):
        self._fill_timed_out_actions()
        return self.log.get_time_remaining_for_action()

    def _fill_timed_out_actions(self):
        # Fills the action log with any needed timed_out actions since our
        # last check. It does not time out the current action we are checking
        when = self.log.get_last_terminating_action_time()
        # Compute how many timed out plies there should be
        diff = now() - when
        missed_plies = diff.seconds / PLY_TIME.seconds
        # Fill in 2 actions per missing ply
        for i in xrange(missed_plies):
            for j in xrange(2):
                then = when + (i + 1) * PLY_TIME
                act = Action(type='timed_out', when=then)
                self._process_action(act)

    def _process_action(self, action):
        num = self.state.num
        action.num = num
        try:
            curr_unit = action.unit.uid
        except AttributeError:
            curr_unit = None
        try:
            prev_unit = self.log.actions[-1].unit.uid
        except (KeyError, IndexError, AttributeError):
            prev_unit = None
        try:
            prev_act = self.log.actions[-1]
        except (KeyError, IndexError):
            prev_act = None

        if action.type != 'timed_out' and self.log.action_timed_out(action):
            action.type = 'timed_out'

        if curr_unit is not None:
            expected_unit = ActionQueue.get_unit_for_action(
                self.battlefield, num).uid
            if curr_unit != expected_unit:
                msg = 'battle: unit {0} is not the expected unit {1}'
                raise BattleError(msg.format(curr_unit, expected_unit))

        if action.type == 'timed_out':
            text = [["Failed to act."]]
            """
            #If this is the first ply, set the second ply to pass as well.
            if action.num % 2 == 1:
                self.process_action(action)
            """

        elif action.type == 'pass':
            text = [["Action Passed."]]
            """
            #If this is the first ply, set the second ply to pass as well.
            if action.num % 2 == 1:
                self.process_action(action)
            """

        elif not num % 2 and prev_unit is not None and prev_unit != curr_unit:
            raise BattleError("Unit from the previous action must be used "
                              "this action.")

        elif action.type == 'move':  # TODO fix move in battlefield.
            # If it's the second action in the ply and
            # it's different from this one.
            if not num % 2:  # if it's the second action in the ply.
                if prev_act.type == 'move':
                    raise BattleError("Second action in ply must be different "
                                      "from first.")
                loc = action.unit.location
                text = self.battlefield.move_scient(loc, action.target)
                if text:
                    text = [[action.unit.uid, action.target]]
            else:
                text = self.battlefield.move_scient(action.unit.location,
                                                    action.target)
                if text:
                    text = [[action.unit.uid, action.target]]

        elif action.type == 'attack':
            # If it's the second action in the ply and
            # it's different from this one.
            if not num % 2:  # if it's the second action in the ply.
                if prev_act.type == 'attack':
                    raise BattleError("Second action in ply must be different "
                                      "from first.")
                text = self.battlefield.attack(action.unit,
                                               action.target)
            else:
                text = self.battlefield.attack(action.unit,
                                               action.target)
        else:
            raise BattleError("Action is of unknown type")

        self.log.actions.append(self.map_action(action))
        self.log.messages.append(Message(num, self.map_result(text)))

        self.state.check(self)
        if not num % 4:
            self.apply_queued()

        result = ActionResult(command=self.log.actions[-1],
                              response=self.log.messages[-1])
        if not num % 4:
            result.applied = self.log.applied[-1]
        return result

    def process_action(self, action):
        """Processes actions sent from battle clients."""
        self._fill_timed_out_actions()
        return self._process_action(action)

    def apply_queued(self):
        """queued damage is applied to units from this state"""
        text = self.battlefield.apply_queued()
        self.log.applied.append(Message(self.state.num,
                                        self.map_result(text)))

    def initial_state(self):
        """Returns stuff to create the client side of the battle"""
        return InitialState(self.log)

    def compute_awards(self, squads):
        awards = []
        for squad in squads:
            for unit in squad:
                if unit.hp <= 0:
                    awards.append(unit.extract_award())
                    if unit.weapon is not None:
                        awards.append(unit.weapon.extract_award())
        return awards

    def _clean_up_dead_units(self, squads):
        """ Removes dead units from their respective locations, and disbands
        the squad if empty """
        for s in squads:
            remove = self._get_dead_units(s)
            for u in remove:
                s.stronghold.remove_unit_from_squad(s.stronghold_pos, u.uid)
            if not s:
                s.stronghold.disband_squad(s.stronghold_pos)

    def _get_victors_and_prisoners(self):
        if self.winner == self.attacker:
            winner = self.battlefield.atksquad
            loser = self.battlefield.defsquad
        else:
            winner = self.battlefield.defsquad
            loser = self.battlefield.atksquad
        victors = PersistentList([u for u in winner if u.hp > 0])
        prisoners = PersistentList([u for u in loser if u.hp > 0])
        return victors, prisoners

    def _get_dead_units(self, squad):
        """ Returns the dead units in squad """
        return [u for u in squad if u.hp <= 0]

    def end(self, condition):
        """ Mame over state, handles log closing,
        writes change list for world"""
        self.state.game_over = True
        self.log.states.append(self.state)
        self.log.close(self.winner, condition)

        # Calculate awards, based on dead units
        awards = self.compute_awards(self.battlefield.squads)

        # Split survivors into victors and prisoners
        victors, prisoners = self._get_victors_and_prisoners()

        # Determine who is dead
        dead_attackers = self._get_dead_units(self.battlefield.atksquad)
        dead_defenders = self._get_dead_units(self.battlefield.defsquad)

        # Record
        u = lambda x: map(attrgetter('uid'), x)
        self.log.change_list = BattleChanges(u(victors), u(prisoners),
                                             u(dead_attackers),
                                             u(dead_defenders),
                                             awards)

        self._clean_up_dead_units([self.battlefield.atksquad,
                                   self.battlefield.defsquad])

        # Update the underlying field
        winner = self.battlefield.atksquad
        if self.winner != winner.owner:
            winner = self.battlefield.defsquad
        self.field.battle_end_callback(self.battlefield.atksquad,
                                       self.battlefield.defsquad,
                                       winner, awards, prisoners)


class ActionQueue(object):

    @classmethod
    def get_player_for_action(cls, battlefield, num):
        """ Returns the player controlling the unit whose action is at action
        num.
        :param units: Living units participating in the battle.
        :param num: Action number sequence """
        return cls.get_unit_for_action(battlefield, num).container.owner

    @classmethod
    def get_unit_for_action(cls, battlefield, num):
        """ Returns the unit whose action is at action num.
        :param units: Living units participating in the battle.
        :param num: Action number sequence """
        if num < 1:
            raise ValueError('Invalid action number {0}'.format(num))
        # action numbers are 1-indexed, set to 0
        num -= 1
        ply = num / 2
        units = cls._get_unit_queue(battlefield)
        queue_pos = ply % len(units)
        return units[queue_pos]

    @classmethod
    def get_action_in_ply(cls, num):
        """ Returns either 0 or 1 """
        return (num - 1) % 2

    @classmethod
    def _get_unit_key(cls, battlefield, unit):
        """Returns a tuple of scalar values to be compared in order"""
        # Sanity checking
        if unit.container is None or unit.container_pos is None:
            raise ValueError('Unit {0} is not in a squad'.format(unit))
        # TODO -- removing this check 'fixed' bad must_rpc logic in demo. -rix
        #if unit.container not in battlefield.squads:
        #    msg = 'Unit {0} is not in a battling squad'
        #    raise ValueError(msg.format(unit))
        if unit.hp <= 0:
            raise ValueError('Unit {} is dead'.format(unit))
        # Lower valued units go first
        val = unit.value
        # Higher counts of the field's primary element go first
        # We invert the value from the max so that a lower value appears
        # in the comparison key
        prime_element_val = 255 - unit.comp[battlefield.element]
        # Earlier placed units in squad go first
        squad_pos = unit.container_pos
        # Attackers go first.  We check is_defender, because False < True
        is_defender = (unit.container == battlefield.defsquad)
        return (val, prime_element_val, squad_pos, is_defender)

    @classmethod
    def _get_unit_queue(cls, battlefield):
        return sorted(battlefield.living_units,
                      key=partial(cls._get_unit_key, battlefield))
