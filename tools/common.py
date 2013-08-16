import os
import sys


def hack_syspath(fn):
    up = os.path.abspath(os.path.join(fn, '../../'))
    sys.path.insert(0, up)
