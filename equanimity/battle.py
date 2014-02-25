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
from persistent.mapping import PersistentMapping
from persistent.list import PersistentList

from battlefield import Battlefield
from units import Unit
from grid import Hex
from const import PLY_TIME
from helpers import now, timestamp
from worldtools import get_world


class BattleError(Exception):
    pass


class Action(PersistentMapping):

    """In a two player game, two actions from a single player make a ply and
       a ply from each player makes a turn. """

    def __init__(self, unit=None, type='pass', target=Hex.null, when=None,
                 num=None):
        if when is None:
            when = now()
        super(Action, self).__init__(unit=unit, type=type, target=target,
                                     num=num, when=when)


class Message(PersistentMapping):

    def __init__(self, num, result):
        super(Message, self).__init__(num=num, result=result, when=now())


class ChangeList(PersistentMapping):
    # TODO - belongs in different file

    def __init__(self, event, **kwargs):
        super(ChangeList, self).__init__(event=event, **kwargs)


class BattleChanges(ChangeList):

    def __init__(self, victors, prisoners, awards, event='battle'):
        super(BattleChanges, self).__init__(event=event, victors=victors,
                                            prisoners=prisoners,
                                            awards=awards)


class InitialState(PersistentMapping):

    """A hack for serialization."""

    def __init__(self, log):
        names = tuple(player.name for player in log['players'])
        super(InitialState, self).__init__(
            init_locs=log['init_locs'], start_time=log['start_time'],
            units=log['units'], grid=log['grid'], owners=log['owners'],
            player_names=names)
        #self['owners'] = self.get_owners(log)


class Log(PersistentMapping):

    def __init__(self, players, units, grid):
        """Records initial game state, timestamps log."""
        super(Log, self).__init__(players=players, units=units, grid=grid)
        self['actions'] = PersistentList()
        self['applied'] = PersistentList()
        self['condition'] = None
        self['change_list'] = None
        self['event'] = 'battle'
        self['end_time'] = None
        self['init_locs'] = None
        self['messages'] = PersistentList()
        self['start_time'] = now()
        self['owners'] = None
        self['states'] = PersistentList()  # Does this really need to be here?
        self['winner'] = None
        self['world_coords'] = None  # set by battle_server
        self['owners'] = self.get_owners()

    def init_locs(self):
        self['init_locs'] = {unit.uid: unit.location for unit in self['units']}

    def close(self, winner, condition):
        """Writes final timestamp, called when game is over."""
        self['end_time'] = now()
        self['winner'] = winner
        self['condition'] = condition

    def get_owners(self):
        """Mapping of unit number to player/owner."""
        return {unit.uid: unit.owner.name for unit in self['units']}

    def last_message(self):
        none = ['There was no message.']
        if not self['messages']:
            return none
        text = self['messages'][-1]['result']
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
                act = self['actions'][-1]
            except IndexError:
                return
            else:
                if act['num'] % 2:
                    term_action = -2
                else:
                    term_action = -1
        elif current_num % 2:
            term_action = -1
        else:
            term_action = -2
        try:
            return self['actions'][term_action]
        except IndexError:
            return

    def get_last_terminating_action_time(self, current_num=None):
        act = self.get_last_terminating_action(current_num=current_num)
        if act is None:
            return self['start_time']
        else:
            return act['when']

    def action_timed_out(self, action):
        start = self.get_last_terminating_action_time(action['num'])
        return (action['when'] - start > PLY_TIME)


class State(PersistentMapping):

    """A dictionary containing the current game state."""

    def __init__(self, game, num=1, pass_count=0, hp_count=0,
                 old_defsquad_hp=0, queued=None, locs=None, HPs=None,
                 game_over=False, **_):
        self.game = game
        if HPs is None:
            HPs = PersistentMapping()
        if queued is None:
            queued = PersistentMapping()
        if locs is None:
            locs = PersistentMapping()
        whose_action = self.game.action_queue.get_player_for_action(num).uid
        super(State, self).__init__(num=num, pass_count=pass_count,
                                    hp_count=hp_count, queued=queued,
                                    old_defsquad_hp=old_defsquad_hp,
                                    locs=locs, HPs=HPs, game_over=game_over,
                                    whose_action=whose_action)

    def check(self, game):
        """Checks for game ending conditions.
        (Assumes two players and no action cue.)"""
        num = self['num']
        last_type = game.log['actions'][num - 1]['type']
        if last_type == 'pass' or last_type == 'timed_out':
            self['pass_count'] += 1
        else:
            self['pass_count'] = 0

        if not num % 4:  # There are 4 actions in a turn.
            # This calcuates hp_count
            defsquad_hp = game.battlefield.defsquad.hp()
            if self['old_defsquad_hp'] >= defsquad_hp:
                self['hp_count'] += 1
            else:
                self['hp_count'] = 0

            # game over check:
            if self['hp_count'] == 4:
                game.winner = game.defender
                return game.end("Attacker failed to deal sufficent damage.")
            else:
                self['old_defsquad_hp'] = defsquad_hp

        # check if game is over.
        if game.battlefield.defsquad.hp() == 0:
            game.winner = game.attacker
            return game.end("Defender's squad is dead")

        if game.battlefield.atksquad.hp() == 0:
            game.winner = game.defender
            return game.end("Attacker's squad is dead")

        if self['pass_count'] >= 8:
            game.winner = game.defender
            return game.end("Both sides passed")

        self['queued'] = game.map_queue()
        self['HPs'], self['locs'] = game.update_unit_info()

        game.log['states'].append(State(game=self.game, **self))

        # game is not over, state is stored, update state.
        self['num'] += 1
        aq = self.game.action_queue
        self['whose_action'] = aq.get_player_for_action(self['num']).uid


class Game(Persistent):

    """Almost-state-machine that maintains game state."""

    def __init__(self, field, attacker):
        super(Game, self).__init__()
        self.field = field
        self.grid = field.grid
        self.defender = field.stronghold.defenders.owner
        self.attacker = attacker.owner
        self.battlefield = Battlefield(field, field.stronghold.defenders,
                                       attacker)
        units = {unit.uid: unit for unit in self.battlefield.units}
        self.map = bidict(units)
        self.units = bidict(inverted(self.map))
        self.winner = None
        self.log = Log(self.players, self.units, self.battlefield.grid)
        self.action_queue = ActionQueue(self)
        self.state = State(self)
        self.state['old_defsquad_hp'] = self.battlefield.defsquad.hp()

    @classmethod
    def get(self, world, field_loc):
        world = get_world(world)
        if world is not None:
            field = world.fields.get(tuple(field_loc))
            if field is not None:
                return field.game

    @property
    def players(self):
        return self.defender, self.attacker

    def start(self):
        self.battlefield.put_squads_on_field()
        self.log.init_locs()

    def timer_view(self):
        num = self.state['num']
        remaining = self.get_time_remaining_for_action()
        current_unit = self.action_queue.get_unit_for_action(num)
        return dict(start_time=timestamp(self.log['start_time']),
                    action_num=self.state['num'],
                    current_ply=self.action_queue.get_action_in_ply(num),
                    current_unit=current_unit.uid,
                    time_remaining=remaining.seconds)

    def api_view(self):
        return dict(
            timer=self.timer_view(),
            defender=self.defender.combatant_view(self.battlefield.defsquad),
            attacker=self.attacker.combatant_view(self.battlefield.atksquad),
            action_num=self.state['num'])

    def map_locs(self):
        """maps unit name unto locations, only returns live units"""
        locs = PersistentMapping()
        for unit in self.units:
            loc = unit.location
            if not loc.is_null():
                locs[unit.uid] = loc
        return locs

    def HPs(self):
        """Hit points by unit."""
        HPs = PersistentMapping()
        for unit in self.units:
            hp = unit.hp
            if hp > 0:
                HPs[unit.uid] = hp
        return HPs

    def update_unit_info(self):
        """returns HPs, Locs."""
        HPs = {}
        locs = {}
        for unit in self.units:
            loc = unit.location
            # TODO (steve) -- should we also check hp > 0 ?
            if not loc.is_null():
                locs[unit.uid] = loc
                HPs[unit.uid] = unit.hp
        return HPs, locs

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

    def map_action(self, **action):
        """replaces unit refrences to referencing their hash.
        TODO (steve) -- this may be unnecessary and cause problems """
        new = Action(**action)
        if new['unit'] is not None:
            new['unit'] = new['unit'].uid
        return new

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
        num = self.state['num']
        action['num'] = num
        try:
            curr_unit = action['unit'].uid
        except AttributeError:
            curr_unit = None
        try:
            prev_unit = self.log['actions'][-1]['unit'].uid
        except (KeyError, IndexError, AttributeError):
            prev_unit = None
        try:
            prev_act = self.log['actions'][-1]
        except (KeyError, IndexError):
            prev_act = None

        if action['type'] != 'timed_out' and self.log.action_timed_out(action):
            action['type'] = 'timed_out'

        if curr_unit is not None:
            expected_unit = self.action_queue.get_unit_for_action(num).uid
            if curr_unit != expected_unit:
                msg = 'battle: unit {0} is not the expected unit {1}'
                raise BattleError(msg.format(curr_unit, expected_unit))

        if action['type'] == 'timed_out':
            text = [["Failed to act."]]
            """
            #If this is the first ply, set the second ply to pass as well.
            if action['num'] % 2 == 1:
                self.process_action(action)
            """

        elif action['type'] == 'pass':
            text = [["Action Passed."]]
            """
            #If this is the first ply, set the second ply to pass as well.
            if action['num'] % 2 == 1:
                self.process_action(action)
            """

        elif not num % 2 and prev_unit is not None and prev_unit != curr_unit:
            raise BattleError("Unit from the previous action must be used "
                              "this action.")

        elif action['type'] == 'move':  # TODO fix move in battlefield.
            # If it's the second action in the ply and
            # it's different from this one.
            if not num % 2:  # if it's the second action in the ply.
                if prev_act['type'] == 'move':
                    raise BattleError("Second action in ply must be different "
                                      "from first.")
                loc = action['unit'].location
                text = self.battlefield.move_scient(loc, action['target'])
                if text:
                    text = [[action['unit'].uid, action['target']]]
            else:
                text = self.battlefield.move_scient(action['unit'].location,
                                                    action['target'])
                if text:
                    text = [[action['unit'].uid, action['target']]]

        elif action['type'] == 'attack':
            # If it's the second action in the ply and
            # it's different from this one.
            if not num % 2:  # if it's the second action in the ply.
                if prev_act['type'] == 'attack':
                    raise BattleError("Second action in ply must be different "
                                      "from first.")
                text = self.battlefield.attack(action['unit'],
                                               action['target'])
            else:
                text = self.battlefield.attack(action['unit'],
                                               action['target'])
        else:
            raise BattleError("Action is of unknown type")

        self.log['actions'].append(self.map_action(**action))
        self.log['messages'].append(Message(num, self.map_result(text)))

        self.state.check(self)
        if not num % 4:
            self.apply_queued()

        result = dict(command=dict(self.log['actions'][-1]),
                      response=dict(self.log['messages'][-1]))
        if not num % 4:
            result['applied'] = dict(self.log['applied'][-1])
        return result

    def process_action(self, action):
        """Processes actions sent from game clients."""
        self._fill_timed_out_actions()
        return self._process_action(action)

    def apply_queued(self):
        """queued damage is applied to units from this state"""
        text = self.battlefield.apply_queued()
        self.log['applied'].append(Message(self.state['num'],
                                           self.map_result(text)))

    def get_last_state(self):
        """Returns the last state in the log."""
        # Figure out if this is actually the *current* state or not, oops.
        try:
            return self.log['states'][-1]
        except (KeyError, IndexError):
            return

    def get_states(self):
        """Returns a list of all previous states."""
        try:
            return self.log['states']
        except KeyError:
            return

    def initial_state(self):
        """Returns stuff to create the client side of the game"""
        return InitialState(self.log)

    def compute_awards(self):
        awards = []
        for squad in self.battlefield.squads:
            for unit in squad:
                if unit.hp <= 0:
                    awards.append(unit.extract_award())
                    if unit.weapon is not None:
                        awards.append(unit.weapon.extract_award())
        return awards

    def clean_up_dead_units(self):
        """ Removes dead units from their respective locations, and disbands
        the squad if empty """
        for s in self.battlefield.squads:
            for u in s:
                if u.hp <= 0:
                    s.stronghold.remove_unit_from_squad(s.stronghold_pos,
                                                        u.uid)
            if not s:
                s.stronghold.disband_squad(s.stronghold_pos)

    def end(self, condition):
        """ Mame over state, handles log closing,
        writes change list for world"""
        self.state['game_over'] = True
        self.log['states'].append(self.state)
        self.log.close(self.winner, condition)
        # make change list
        victors = PersistentList()
        prisoners = PersistentList()

        # split survivors into victors and prisoners
        for unit in self.log['states'][-1]['HPs']:
            if self.log['owners'][unit.uid] == self.winner.name:
                victors.append(unit)
            else:
                prisoners.append(unit)

        # calculate awards
        awards = self.compute_awards()
        self.field.stronghold.silo.imbue_list(awards)
        self.log['change_list'] = BattleChanges(victors, prisoners, awards)

        self.clean_up_dead_units()

        if self.winner == self.attacker:
            # Attempt to capture the field. It will fail if the stronghold
            # is still garrisoned.
            self.field.get_taken_over(self.battlefield.atksquad)
        else:
            # Prisoners must be transferred from attacker to defender's
            # stronghold's free units
            # If prisoners cannot fit they return to where they came from
            for u in prisoners:
                # TODO -- handle stronghold capacity limits
                self.field.stronghold.add_free_unit(u)
        # Allow the world to take over if the defender is vacant
        self.field.check_ungarrisoned()


class ActionQueue(Persistent):

    def __init__(self, game):
        super(ActionQueue, self).__init__()
        self.game = game
        self.units = self._get_unit_queue(self.game.battlefield.units)

    def get_player_for_action(self, num):
        return self.get_unit_for_action(num).container.owner

    def get_unit_for_action(self, num):
        if num < 1:
            raise ValueError('Invalid action number {0}'.format(num))
        # action numbers are 1-indexed, set to 0
        num -= 1
        ply = num / 2
        queue_pos = ply % len(self.units)
        return self.units[queue_pos]

    def get_action_in_ply(self, num):
        """ Return either 0 or 1 """
        return (num - 1) % 2

    def _get_unit_key(self, unit):
        """Returns a tuple of scalar values to be compared in order"""
        # Sanity checking
        if unit.container is None or unit.container_pos is None:
            raise ValueError('Unit {0} is not in a squad'.format(unit))
        if unit.container not in self.game.battlefield.squads:
            msg = 'Unit {0} is not in a battling squad'
            raise ValueError(msg.format(unit))
        # Lower valued units go first
        val = unit.value()
        # Higher counts of the field's primary element go first
        # We invert the value from the max so that a lower value appears
        # in the comparison key
        prime_element_val = 255 - unit.comp[self.game.battlefield.element]
        # Earlier placed units in squad go first
        squad_pos = unit.container_pos
        # Attackers go first.  We check is_defender, because False < True
        is_defender = (unit.container == self.game.battlefield.defsquad)
        return (val, prime_element_val, squad_pos, is_defender)

    def _get_unit_queue(self, units):
        return sorted(units, key=self._get_unit_key)
