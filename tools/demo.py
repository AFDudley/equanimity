#!/usr/bin/env python

from common import hack_syspath
hack_syspath(__file__)

import transaction
import random
from argparse import ArgumentParser
from itertools import ifilter
from client import EquanimityClient
from equanimity.grid import Grid, Hex
from equanimity.field import Field
from server.decorators import script
import ipdb
import sys
import time

def get_args():
    p = ArgumentParser(prog='Equanimity Demo')
    p.add_argument('--config', default='dev', help='Server config file to use')
    p.add_argument('--url', default='http://127.0.0.1:5000/',
                   help='URL of server')
    return p.parse_args()


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
    vid = v['result']['vestibule']['uid']
    print 'Join vestibule'
    q.must_rpc('vestibule.join', vid)
    print 'Start vestibule'
    try:
        p.rpc('vestibule.start', vid)
    except Exception as e:
        print e
        sys.exc_clear()
    return vid
    
def force_start_battle(wid, df):
    # Field clock must tick.  There is no RPC to force the clock to tick,
    # so we import it here.  We also bypass the time counting, and forecfully
    # advance the field's day (this only processes the field queue)
    f = Field.get(wid, df['coordinate'])
    if not f.queue.queue:
        raise ValueError("Field queue is empty")
    f.clock.change_day(f)
    transaction.commit()


def find_first(predicate, seq):
    return next(ifilter(predicate, seq), None)


def get_adjacent_enemy_fields(fields, p, q):
    # All visible enemy fields are adjacent to one of ours, so pick one of
    # those first
    df = find_first(lambda f: f['owner'] == q.player['uid'], fields)
    if df is None:
        raise ValueError('No defender found to be attacked')

    # Pick any field of the attacker's that is adjacent
    def matches(f):
        adj = Grid.is_adjacent(f['coordinate'], df['coordinate'])
        return f['owner'] == p.player['uid'] and adj

    af = find_first(matches, fields)
    if af is None:
        raise ValueError('No adjacent attacking field for chosen defender')

    return df, af


def get_stronghold_squad(wid, stronghold, p):
    squad = None
    if stronghold['squads']:
        squad = stronghold['squads'][0]
    else:
        if stronghold['free']:
            units = [u['uid'] for u in stronghold['free']]
            sq = p.must_rpc('stronghold.form_squad', wid,
                            stronghold['field'], units)
            squad = sq['result']['squad']
        else:
            raise ValueError('No squads, no free units')
    if squad is None:
        raise ValueError('Could not find a squad')
    return squad


def move_squad(wid, squad, df, af, p):
    delta = [df['coordinate'][i] - c for i, c in enumerate(af['coordinate'])]
    direction = Grid.vectors[:Hex._make(delta)]
    squad = p.must_rpc('stronghold.move_squad', wid, af['coordinate'],
                       squad['stronghold_pos'], direction)
    squad = squad['result']['squad']
    if squad['queued_field'] != df['coordinate']:
        raise ValueError('Attacking squad is not queued to attack')


def _setup_battle(wid, p, q):
    # Get world info so we can choose two fields with enemies adjacent
    world = p.must_rpc('info.world', wid)['result']['world']
    fields = world['visible_fields']
    print "Fields: {0}".format(fields)
    # Get two adjacent fields, so p can attack
    df, af = get_adjacent_enemy_fields(fields, p, q)

    # Get the attacker's stronghold info
    astr = p.must_rpc('info.stronghold', wid, af['coordinate'])
    astr = astr['result']['stronghold']

    # Get the attacking squad
    asq = get_stronghold_squad(wid, astr, p)

    # Choose the attacking scient's position on the field
    for i, uid in enumerate(asq['units']):
        p.must_rpc('stronghold.place_unit', uid, [i + 1, 0])

    # Get the defender's stronghold info
    dstr = q.must_rpc('info.stronghold', wid, df['coordinate'])
    dstr = dstr['result']['stronghold']

    # Get the defending squad
    dsq = get_stronghold_squad(wid, dstr, q)

    # Choose the defender's position on the field so that it is easy to kill
    for i, uid in enumerate(dsq['units']):
        q.must_rpc('stronghold.place_unit', uid, [i + 1, 0])

    # Move squad from p's field to q's
    move_squad(wid, asq, df, af, p)

    # Make sure we see the attacking squad in the defending field queue
    df = q.must_rpc('info.field', wid, df['coordinate'])
    df = df['result']['field']
    print "attacking squad: {0}".format(df['queue'])
    if not df['queue']:
        raise ValueError("No attacking squad in defending field queue")

    return af, df


def attack_or_move(wid, df, p, au, du):
    print 'Attacking or moving'
    r = p.rpc('battle.attack', wid, df['coordinate'], au['uid'],
              du['location'])
    if r.get('error') is not None:
        print 'Failed to attack:'
        print r['error']
        print 'Moving instead'
        # Move and pass
        pos = au['location']
        moved = False
        vectors = Grid.inverted_vectors.keys()
        random.shuffle(vectors)
        for v in vectors:
            pos[0] += v.q
            pos[1] += v.r
            r = p.rpc('battle.move', wid, df['coordinate'], au['uid'],
                      pos)
            if r.get('error') is None:
                print 'Moved to ', pos
                au['location'] = pos
                moved = True
                break
            else:
                print 'Movement attempt to {} failed'.format(v)
        if not moved:
            print 'Couldn\'t move, doing an extra pass'
            p.must_rpc('battle.pass', wid, df['coordinate'],
                       au['uid'])
    p.must_rpc('battle.pass', wid, df['coordinate'], au['uid'])


def pass_all(wid, df, q, du):
    print 'Passing all defender moves'
    for i in range(2):
        q.rpc('battle.pass', wid, df['coordinate'], du['uid'])


def _battle(wid, df, p, q, battle):
    """ The actual battle """
    world = p.must_rpc('info.world', wid)['result']['world']
    asq = battle['attacker']['squad']
    dsq = battle['defender']['squad']
    au = asq['units'][0]
    du = dsq['units'][0]

    t = p.must_rpc('info.battle_timer', battle['uid'])
    t = t['result']['battle']['timer']

    actions = [
        lambda: attack_or_move(wid, df, p, au, du),
        lambda: pass_all(wid, df, q, du),
    ]
    if t['current_unit'] == du['uid']:
        actions.reverse()

    # Move around until we are in range
    while True:
        for a in actions:
            a()
        print 'Checking battle status'
        r = p.must_rpc('info.battle', battle['uid'])
        battle = r['result']['battle']
        if battle['game_over']:
            print 'Battle is over'
            print battle
            break


def battle(wid, df, p, q):
    # p kills everything of q's

    # Get battle, field info
    # Move sword from to q's units, attacking when possible
    # Have q pass every turn
    # Once we've won, we should own the stronghold

    print 'Getting battle info'
    battle = p.must_rpc('info.field_battle', wid, df['coordinate'])
    battle = battle['result']['battle']
    print battle
    print 'Attacker unit count:', len(battle['attacker']['squad']['units'])
    print 'Defender unit count:', len(battle['defender']['squad']['units'])

    print 'Attacking'
    _battle(wid, df, p, q, battle)


def setup_battle(wid, p, q):
    """checks if world has fields"""
    print p.must_rpc('info.world_has_fields', wid)['result']['has_fields']
    if p.must_rpc('info.world_has_fields', wid)['result']['has_fields']:
        _, df = _setup_battle(wid, p, q)
        print "df inside setup battle: {0}".format(df)
        return df
    else:
        print "checking for fields in 5 seconds..."
        time.sleep(5)
        setup_battle(wid, p, q)        
   
    
def run_demo(config, url):
    p = EquanimityClient(url=url)
    q = EquanimityClient(url=url)
    # Create two players
    create_player(p, 'atkr', 'atkrpassword', 'atkr@example.com')
    create_player(q, 'dfdr', 'dfdrpassword', 'dfdr@example.com')
    # Start the game via the vestibule
    vid = start_game(p, q)
    
    wid = p.must_rpc('vestibule.get', vid)['result']['vestibule']['world']
    world = p.must_rpc('info.world', wid)['result']['world']
    df = setup_battle(wid, p, q)
    # Update the world clock so that the battle starts
    print 'Forcing battle start'
    script(config=config)(force_start_battle)(world, df)
    battle(world, df, p, q)

if __name__ == '__main__':
    args = get_args()
    run_demo(args.config, args.url)
