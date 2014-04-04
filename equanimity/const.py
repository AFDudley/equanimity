"""
const.py

Created by AFD on 2013-08-05.
Copyright (c) 2013 A. Frederick Dudley. All rights reserved.
"""

from datetime import timedelta

E = 'Earth'
F = 'Fire'
I = 'Ice'
W = 'Wind'

ELEMENTS = (E, F, I, W)

ORTH = {E: (F, I),   # Earth is orthogonal to Fire and Ice
        F: (E, W),   # Fire  is orthogonal to Earth and Wind
        I: (E, W),   # Ice   is orthogonal to Earth and Wind
        W: (F, I)}  # Wind  is orthogonal to Fire and Ice

OPP = {E: W, W: E,   # Earth and Wind are opposites
       F: I, I: F}   # Fire and Ice are opposites

COMP = {E: 0, F: 0, I: 0, W: 0}
WEP_LIST = ('Sword', 'Bow', 'Wand', 'Glove')
WEP_BONUS = {'Sword': 0, 'Bow': 0, 'Wand': 0, 'Glove': 0}
EQUIP_LIMIT = {'Sword': 1, 'Bow': 1, 'Wand': 1, 'Glove': 1}

KINDS = ('Stone', 'Weapon', 'Nescient', 'Scient')
UNIT_KINDS = ('Nescient', 'Scient')
SEX = ('female', 'male')
OPPSEX = {'female': 'male', 'male': 'female'}

WORLD_UID = 0
PLY_MINUTES=4
PLY_TIME = timedelta(minutes=PLY_MINUTES)

LETTERS = {E[0]: E, F[0]: F, I[0]: I, W[0]: W}

CLOCK = dict(
    generation=timedelta(minutes=PLY_MINUTES*5040),
    year=timedelta(minutes=PLY_MINUTES*360),
    season=timedelta(minutes=PLY_MINUTES*120),
    month=timedelta(minutes=PLY_MINUTES*30),
    week=timedelta(minutes=PLY_MINUTES*6),
    day=timedelta(minutes=PLY_MINUTES)
)

FIELD_PRODUCE = 'produce'
FIELD_YIELD = 'yield'
FIELD_BATTLE = 'battle'
