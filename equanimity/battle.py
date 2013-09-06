"""
battle.py

Created by AFD on 2013-08-05.
Copyright (c) 2013 A. Frederick Dudley. All rights reserved.
"""
"""
This needs to be refactored to properly generate json/serialized output
and should be refactored with battle as well.

"""
from datetime import datetime

import transaction
from persistent import Persistent
from persistent.mapping import PersistentMapping
from persistent.list import PersistentList

from grid import Grid
from battlefield import Battlefield
from units import Unit


def now():
    return str(datetime.utcnow())


class Action(PersistentMapping):
    #'when' needs more thought.
    #type needs to != 'pass'
    """In a two player game, two actions from a single player make a ply and
       a ply from each player makes a turn. """
    def __init__(self, unit=None, type='pass', target=None, when=None,
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
        self['owners'] = None
        self['start_time'] = now()
        self['states'] = PersistentList()  # Does this really need to be here?
        self['winner'] = None
        self['world_coords'] = None  # set by battle_server

    def init_locs(self):
        #calling this in init is most likely not going to work as intended.
        locs = PersistentMapping()
        for u in self['units']:
            locs.update({u: self['units'][u].location})
        return locs

    def close(self, winner, condition):
        """Writes final timestamp, called when game is over."""
        self['end_time'] = now()
        self['winner'] = winner
        self['condition'] = condition

    def get_owner(self, unit_num):
        """takes unit number returns player/owner."""
        # slow lookup
        owner = None
        target_squad = self['units'][unit_num].container.name
        for player in self['players']:
            for squad in player.squads:
                if squad.name == target_squad:
                    owner = player
        return owner

    #LAZE BEAMS!!!!
    def get_owners(self):
        """mapping of unit number to player/owner."""
        owners = PersistentMapping()
        for unit in self['units']:
            owners[unit] = self.get_owner(unit).name
        return owners


class State(PersistentMapping):

    phases = ['unit_placement', 'combat']

    """A dictionary containing the current game state."""
    def __init__(self, game, num=1, pass_count=0, hp_count=0,
                 old_defsquad_hp=0, queued=None, locs=None, HPs=None,
                 game_over=False, whose_action=None):
        self.game = game
        if HPs is None:
            HPs = PersistentMapping()
        if queued is None:
            queued = PersistentMapping()
        if locs is None:
            locs = PersistentMapping()
        if phase is None:
            if phase not in self.phases:
                raise ValueError('Invalid phase {0}'.format(phase))
            phase = 'unit_placement'
        super(State, self).__init__(num=num, pass_count=pass_count,
                                    hp_count=hp_count, queued=queued,
                                    old_defsquad_hp=old_defsquad_hp,
                                    locs=locs, HPs=HPs, game_over=game_over,
                                    whose_action=whose_action, phase=phase)

    def check(self, game):
        if self['phase'] != 'combat':
            return
        """Checks for game ending conditions.
        (Assumes two players and no action cue.)"""
        num = self['num']
        last_type = game.log['actions'][num - 1]['type']
        if last_type == 'pass' or last_type == 'timed_out':
            self['pass_count'] += 1
        else:
            self['pass_count'] = 0

        if not num % 4:  # There are 4 actions in a turn.
            #This calcuates hp_count
            defsquad_hp = game.battlefield.defsquad.hp()
            if self['old_defsquad_hp'] >= defsquad_hp:
                self['hp_count'] += 1
            else:
                self['hp_count'] = 0

            #game over check:
            if self['hp_count'] == 4:
                game.winner = game.defender
                return game.end("Attacker failed to deal sufficent damage.")
            else:
                self['old_defsquad_hp'] = defsquad_hp

        #check if game is over.
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

        #game is not over, state is stored, update state.
        self['num'] += 1
        self['whose_action'] = self.get_player_for_action(self['num']).id
        transaction.commit()

    def start_combat(self, action_queue):
        if self.phase == 'combat':
            raise ValueError('Phase is already in combat')
        self['whose_action'] = self.get_player_for_action(self['num']).id


class Game(Persistent):
    """Almost-state-machine that maintains game state."""
    def __init__(self, attacker, defender, grid=None, element=None):
        super(Game, self).__init__()
        if grid is None:
            grid = Grid()
        self.grid = grid
        self.defender = defender
        self.attacker = attacker
        self.battlefield = Battlefield(grid, self.defender.squads[0],
                                       self.attacker.squads[0],
                                       element=element)
        self.state = State(self)

        self.players = self.defender, self.attacker
        # TODO (steve) -- bidirectional map instead of map,units
        self.map = self.unit_map()
        self.units = self.map_unit()
        self.winner = None
        self.log = Log(self.players, self.units, self.battlefield.grid)
        self.log['owners'] = self.log.get_owners()
        self.state['old_defsquad_hp'] = self.battlefield.defsquad.hp()
        self.action_queue = ActionQueue(self)
        return transaction.commit()

    def put_squads_on_field(self):
        """Puts the squads on the battlefield."""
        btl = self.battlefield
        for squad_num, squad in enumerate(btl.squads):
            for unit_num, unit in enumerate(squad):
                # If the unit was already placed, it's ok
                # This is to assert that all units are in place or receive
                # a valid place
                btl.place_object(unit, unit.location)
        self.log['init_locs'] = self.log.init_locs()
        return transaction.commit()

    def unit_map(self):
        """mapping of unit ids to objects, used for serialization."""
        mapping = PersistentMapping()
        for unit in self.battlefield.units:
            mapping[unit] = unit.id
        return mapping

    def map_unit(self):
        units = PersistentMapping()
        for k, v in self.map.iteritems():
            units[v] = k
        return units

    def map_locs(self):
        """maps unit name unto locations, only returns live units"""
        locs = PersistentMapping()
        for unit in self.map:
            loc = unit.location
            if not loc.is_null():
                locs[self.map[unit]] = loc
        return locs

    def HPs(self):
        """Hit points by unit."""
        HPs = PersistentMapping()
        for unit in self.map:
            hp = unit.hp
            if hp > 0:
                HPs[self.map[unit]] = hp
        return HPs

    def update_unit_info(self):
        """returns HPs, Locs."""
        HPs = {}
        locs = {}
        for unit, num in self.map.iteritems():
            loc = unit.location
            # TODO (steve) -- should we also check hp > 0 ?
            if not loc.is_null():
                locs[num] = loc
                HPs[num] = unit.hp
        return HPs, locs

    def map_queue(self):
        """apply unit mapping to units in queue."""
        queue = self.battlefield.get_dmg_queue()
        return {key.id: val for key, val in queue.iteritems()}

    def map_result(self, result):
        for t in result:
            if isinstance(t[0], Unit):
                t[0] = t[0].id
        return result

    def map_action(self, **action):
        """replaces unit refrences to referencing their hash."""
        new = Action(**action)
        if new['unit'] is not None:
            new['unit'] = new['unit'].id
        return new

    def last_message(self):
        none = ["There was no message."]
        if not self.log['messages']:
            return none
        text = self.log['messages'][-1]['result']
        if text is None:
            return none
        return text

    def process_action(self, action):
        # TODO (steve) -- check that 1st, 2nd plies are from attacker,
        # and that 3rd, 4th plies are from defender
        # and that action['unit'] matches the action queue's order

        """Processes actions sent from game clients."""
        # Needs more logic for handling turns/plies.
        action['when'] = now()
        num = action['num'] = self.state['num']
        try:
            curr_unit = action['unit'].id
        except AttributeError:
            curr_unit = None
        try:
            prev_unit = self.log['actions'][-1]['unit'].id
        except (KeyError, IndexError, AttributeError):
            prev_unit = None
        try:
            prev_act = self.log['actions'][-1]['type']
        except (KeyError, IndexError):
            prev_act = None

        expected_unit = self.action_queue.get_unit_for_action(num)
        if curr_unit != expected_unit:
            msg = 'battle: unit {0} is not the expected unit {1}'
            raise ValueError(msg.format(curr_unit, expected_unit))

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
            raise ValueError("battle: Unit from the previous action must be "
                             "used this action.")

        elif action['type'] == 'move':  # TODO fix move in battlefield.
            # If it's the second action in the ply and
            # it's different from this one.
            if not num % 2:  # if it's the second action in the ply.
                if prev_act == 'move':
                    raise ValueError("battle: Second action in ply must be "
                                     "different from first.")
                loc = action['unit'].location
                text = self.battlefield.move_scient(loc, action['target'])
                if text:
                    text = [[action['unit'].id, action['target']]]
            else:
                text = self.battlefield.move_scient(action['unit'].location,
                                                    action['target'])
                if text:
                    text = [[action['unit'].id, action['target']]]

        elif action['type'] == 'attack':
            # If it's the second action in the ply and
            # it's different from this one.
            if not num % 2:  # if it's the second action in the ply.
                if prev_act == 'attack':
                    raise ValueError("battle: Second action in ply must be "
                                     "different from first.")
                text = self.battlefield.attack(action['unit'],
                                               action['target'])
            else:
                text = self.battlefield.attack(action['unit'],
                                               action['target'])
        else:
            raise ValueError("battle: Action is of unknown type")

        self.log['actions'].append(self.map_action(**action))
        self.log['messages'].append(Message(num, self.map_result(text)))

        if not num % 4:
            self.apply_queued()
        else:
            self.state.check(self)

        transaction.commit()

        result = dict(command=dict(self.log['actions'][-1]),
                      response=dict(self.log['messages'][-1]))
        if not num % 4:
            result['applied'] = dict(self.log['applied'][-1])
        return result

    def apply_queued(self):
        """queued damage is applied to units from this state"""
        text = self.battlefield.apply_queued()
        self.log['applied'].append(Message(self.state['num'],
                                           self.map_result(text)))
        self.state.check(self)

    def get_last_state(self):
        """Returns the last state in the log."""
        #Figure out if this is actually the *current* state or not, oops.
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
            if self.log['owners'][unit.id] == self.winner.name:
                victors.append(unit)
            else:
                prisoners.append(unit)
        # calculate awards
        awards = PersistentMapping()  # should be a stone.
        self.log['change_list'] = BattleChanges(victors, prisoners, awards)


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
