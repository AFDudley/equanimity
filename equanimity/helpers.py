"""
helpers.py

Created by AFD on 2013-08-05.
Copyright (c) 2013 A. Frederick Dudley. All rights reserved.
"""
"""Helper functions"""
import random
import string
from const import ELEMENTS
from datetime import datetime


def validate_length(seq, **limits):
    if not limits['min'] <= len(seq) <= limits['max']:
        raise ValueError('Invalid sequence length {0}'.format(len(seq)))


def rand_string(len=8):
    return ''.join(random.choice(string.letters) for i in xrange(len))


def rand_element():
    """Reuturns a random element"""
    return random.choice(ELEMENTS)


def now():
    return datetime.utcnow()
