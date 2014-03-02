#!/usr/bin/env python

from common import hack_syspath
hack_syspath(__file__)

import transaction
from client import EquanimityClient
from equanimity.grid import Grid, Hex
from equanimity.world import World
from server.decorators import script


def create_player(c, username, password, email):
    """ Creates a player and logs in """
    # Signup, to make sure the account exists
    print 'Signup'
    c.signup(username, password, email)
    # Login
    print 'Login'
    c.login(username, password)


def start_game(p, q):
    """ Creates a vestibule, adds the second player and starts a game """
    # Setup the vestibule
    print 'Create vestibule'
    v = p.must_rpc('vestibule.create')
    id = v['result']['vestibule']['uid']
    print 'Join vestibule'
    q.rpc('vestibule.join', id)
    print 'Start vestibule'
    world = p.must_rpc('vestibule.start', id)
    return world['result']['world']


@script()
def tick_clock(world):
    # Field clock must tick.  There is no RPC to force the clock to tick,
    # so we import it here.
    w = World.get(world['uid'])
    w.clock.tick(w.fields)
    transaction.commit()


def get_adjacent_enemy_fields(fields, p, q):
    # All visible enemy fields are adjacent to one of ours, so pick one of
    # those first
    df = None
    for f in fields:
        if f['owner'] == q.player['uid']:
            df = f
            break
    if df is None:
        raise ValueError('No defender found to be attacked')

    # Pick any field of the attacker's that is adjacent
    af = None
    for f in fields:
        adj = Grid.is_adjacent(f['coordinate'], df['coordinate'])
        if f['owner'] == p.player['uid'] and adj:
            af = f
            break
    if af is None:
        raise ValueError('No adjacent attacking field for chosen defender')

    return df, af


def get_attacking_squad(world, stronghold, p, af):
    squad = None
    if stronghold['squads']:
        squad = stronghold['squads'][0]
    else:
        if stronghold['free_units']:
            units = [u['uid'] for u in stronghold['free_units']]
            sq = p.must_rpc('stronghold.form_squad', world['uid'],
                            af['coordinate'], units)
            squad = sq['result']['squad']
        else:
            raise ValueError('No squads, no free units')
    if squad is None:
        raise ValueError('Could not acquire an attacking squad')
    return squad


def move_squad(world, squad, df, af, p):
    delta = [df['coordinate'][i] - c for i, c in enumerate(af['coordinate'])]
    direction = Grid.vectors[:Hex._make(delta)]
    squad = p.must_rpc('stronghold.move_squad', world['uid'], af['coordinate'],
                       squad['stronghold_pos'], direction)
    squad = squad['result']['squad']
    if squad['queued_field'] != df['coordinate']:
        raise ValueError('Attacking squad is not queued to attack')


def setup_battle(world, p, q):
    # Get world info so we can choose two fields with enemies adjacent
    world = p.must_rpc('info.world', world['uid'])['result']['world']
    fields = world['visible_fields']

    # Get two adjacent fields, so p can attack
    df, af = get_adjacent_enemy_fields(fields, p, q)

    # Get the attacker's stronghold info
    stronghold = p.must_rpc('info.stronghold', world['uid'], af['coordinate'])
    stronghold = stronghold['result']['stronghold']

    # Get the attacking squad
    squad = get_attacking_squad(world, stronghold, p, af)

    # Move squad from p's field to q's
    move_squad(world, squad, df, af, p)

    # Update the world clock so that the battle starts
    tick_clock(world)


def battle(p, q):
    # p kills everything of q's

    # Get battle, field info
    # Move sword from to q's units, attacking when possible
    # Have q pass every turn
    # Once we've won, we should own the stronghold

    pass


def run_demo():
    p = EquanimityClient()
    q = EquanimityClient()
    # Create two players
    create_player(p, 'atkr', 'atkrpassword', 'atkr@example.com')
    print 'P Cookies', p.cookies
    create_player(q, 'dfdr', 'dfdrpassword', 'dfdr@example.com')
    print 'Q Cookies', q.cookies
    # Start the game via the vestibule
    world = start_game(p, q)
    print 'World', world

    # How to initiate a battle?
    # Move squad?
    setup_battle(world, p, q)

    battle(p, q)

if __name__ == '__main__':
    run_demo()
