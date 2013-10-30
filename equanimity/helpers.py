"""
helpers.py

Created by AFD on 2013-08-05.
Copyright (c) 2013 A. Frederick Dudley. All rights reserved.
"""
"""Helper functions"""
import random
import string
from functools import wraps
from threading import Lock
from const import ELEMENTS
from calendar import timegm
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
    """ Returns the current UTC datetime"""
    return datetime.utcnow()


def timestamp(dt):
    """ Returns a date as a unix timestamp """
    return timegm(dt.utctimetuple())


def atomic(f):
    """ Locks a function when called.  BE CAREFUL -- deadlocks """
    lock = Lock()

    @wraps(f)
    def wrapped(*args, **kwargs):
        with lock:
            return f(*args, **kwargs)
    return wrapped


class classproperty(object):
    """ @property + @classmethod """

    def __init__(self, getter):
        self._getter = getter

    def __get__(self, instance, owner):
        return self._getter(owner)
