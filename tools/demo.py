#!/usr/bin/env python

from common import hack_syspath
hack_syspath(__file__)

from client import EquanimityClient


def create_player(c, username, password, email):
    """ Creates a player and logs in """
    # Signup, to make sure the account exists
    print 'Signup'
    print c.signup(username, password, email)
    # Login
    print 'Login'
    print c.login(username, password)


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


def start_battle(world, p, q):
    # p moves a squad to an adjacent q field
    # then somehow the field clock is advanced and a battle is initiated

    # Get world info and find adjacent enemy fields
    # Get stronghold info for the stronghold there, extract a squad
    # Move the squad from that stronghold to the adjacent one TODO move_squad
    # Somehow get the clock to advance so the battle starts??

    print p.must_rpc('info.world', world['uid'])


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
    start_battle(world, p, q)

    battle(p, q)

if __name__ == '__main__':
    run_demo()
