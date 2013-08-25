"""
helpers.py

Created by AFD on 2013-08-05.
Copyright (c) 2013 A. Frederick Dudley. All rights reserved.
"""
"""Helper functions"""
import random
import string
from const import ELEMENTS, ORTH, KINDS, OPP
from stone import Stone
from units import Scient, Nescient
from unit_container import Squad
from operator import itemgetter


def rand_string(len=8):
    return ''.join(random.choice(string.letters) for i in xrange(len))


def t2c(tup):
    """Converts a tuple to a comp"""
    if len(tup) != 4:
        raise Exception("Incorrect number of values in tuple")
    comp = Stone()
    for i in range(4):
        comp[ELEMENTS[i]] = tup[i]
    return comp


def rand_element():
    """Reuturns a random element"""
    return random.choice(ELEMENTS)


def get_element(comp):
    """Gets the primary element from a comp, or choses at random from equals.
    """
    sort = sorted(comp.iteritems(), key=itemgetter(1), reverse=True)
    if sort[0][1] == sort[3][1]:  # they are all equal
        return random.choice(sort)[0]
    elif sort[0][1] == sort[2][1]:
        return random.choice(sort[:3])[0]
    elif sort[0][1] == sort[1][1]:
        return random.choice(sort[:2])[0]
    else:
        return sort[0][0]


def max_comp(suit, kind='Scient'):
    """Returns the maximum composition of 'kind' of element 'suit'"""
    comp = Stone()
    if kind == 'Scient':
        comp[suit] = 255
        comp[OPP[suit]] = 0
        comp[ORTH[suit][0]] = comp[ORTH[suit][1]] = 127
        return comp
    if kind == 'Weapon':
        comp2 = Stone()
        comp2[suit] = comp[suit] = 63
        comp2[OPP[suit]] = comp[OPP[suit]] = 0
        comp2[ORTH[suit][0]] = comp[ORTH[suit][1]] = 0
        comp2[ORTH[suit][1]] = comp[ORTH[suit][0]] = 63
        return (comp, comp2)
    if kind == 'Nescient':
        comp2 = Stone()
        comp2[suit] = comp[suit] = 255
        comp2[OPP[suit]] = comp[OPP[suit]] = 0
        comp2[ORTH[suit][0]] = comp[ORTH[suit][1]] = 0
        comp2[ORTH[suit][1]] = comp[ORTH[suit][0]] = 254
        return (comp, comp2)
    if kind == 'Stone':
        for i in comp:
            comp[i] = 255
        return comp


def rand_comp(suit=None, kind=None, max_v=255):
    """Returns a random comp in 'suit' for use instaniating 'kind'
       If 'suit' is not valid, random element used.
       If 'kind' is not valid stone is used
       if 'kind' is 'Stone' suit ignored"""
    if not suit in ELEMENTS:
        suit = rand_element()

    comp = Stone()
    if kind is None or kind not in KINDS:
        kind = 'Stone'

    if kind == 'Stone':
        for element in comp:
            comp[element] = random.randint(0, max_v)
        return comp
    else:
        if kind == 'Scient':
            comp[suit] = random.randint(1, max_v)
            for picked in ORTH[suit]:
                # NOTE: if comp[suit] = 1 orths will be 0.
                comp[picked] = random.randint(0, (comp[suit] / 2))
            return comp

        else:  # Nescient is currently the only other kind
            comp[suit] = random.randint(1, max_v)
            comp[random.choice(ORTH[suit])] = \
                random.randint(1, comp[suit])
            return comp


def rand_unit(suit=None, kind='Scient'):
    """Returns a random Scient of suit. Random suit used if none given."""
    kinds = ('Scient', 'Nescient')
    if not kind in kinds:
        kind = random.choice(kinds)

    if not suit in ELEMENTS:
        suit = rand_element()
        comp = rand_comp(suit, kind)
    else:
        comp = rand_comp(suit, kind)

    if kind == 'Scient':
        return Scient(suit, comp, rand_string())
    else:
        return Nescient(suit, rand_comp(suit, 'Nescient'), rand_string())


def rand_squad(suit=None, kind='Scient'):
    """Returns a Squad of five random Scients of suit. Random suit used
       if none given."""
    #please clean me up.
    squad = Squad()
    if kind == 'Scient':
        size = 5
        if not suit in ELEMENTS:
            for _ in range(size):
                squad.append(rand_unit(rand_element(), kind))
        else:
            for _ in range(size):
                squad.append(rand_unit(suit, kind))
    else:
        if not suit in ELEMENTS:
            while squad.free_spaces >= 2:
                squad.append(rand_unit(rand_element()))
            if squad.free_spaces == 1:
                squad.append(rand_unit(rand_element(), kind='Scient'))
        else:
            while squad.free_spaces >= 2:
                squad.append(rand_unit(suit))
            if squad.free_spaces == 1:
                squad.append(rand_unit(suit, kind='Scient'))
    squad.name = rand_string()
    return squad


def print_rand_squad(suit=None):
    squad = rand_squad(suit)
    for unit in squad:
        print unit
    return squad


def show_squad(squad):
    print squad(more=1)


def max_squad_by_value(value):
    """Takes an integer, ideally even because we round down, and returns a
    squad such that comp[element] == value, comp[orth] == value/2, comp[opp]
    == 0"""
    squad = Squad()
    value = value / 2  # more logical, really.
    half = value / 2
    for i in ELEMENTS:
        s = Stone()
        s[i] = value
        s[OPP[i]] = 0
        for o in ORTH[i]:
            s[o] = half
        squad.append(Scient(i, s))
    return squad


def one_three_zeros(value):
    squad = Squad()
    for i in ELEMENTS:
        s = Stone()
        s[i] = value
        squad.append(Scient(i, s))
    return squad


def stats(unit):
    print unit.name + ": " + str(unit.comp)
    print "Physical: " + str(unit.p)
    print "Magical: " + str(unit.m)
    print "Attack: " + str(unit.atk)
    print "Defense: " + str(unit.defe)
    print "P ATK: " + str(unit.patk)
    print "P DEF: " + str(unit.pdef)
    print "M ATK: " + str(unit.matk)
    print "M DEF: " + str(unit.mdef)
