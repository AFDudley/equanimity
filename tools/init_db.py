#!/usr/bin/env python

from common import hack_syspath
hack_syspath(__file__)

import transaction
import argparse
from persistent import Persistent
from BTrees.OOBTree import OOBTree
from BTrees.IOBTree import IOBTree
from server import db, create_app
from equanimity.db import AutoID


def init_db(reset=False, verbose=False):
    start = dict(player_uid=AutoID('player'),
                 player=IOBTree(),           # maps uid (int) -> Player
                 player_username=OOBTree(),  # maps username (str) -> Player
                 player_email=OOBTree())     # maps email (str) -> Player
    for k, v in start.iteritems():
        if reset:
            db[k] = v
        else:
            db.setdefault(k, v)
        if verbose:
            print k, db[k]


def get_args():
    p = argparse.ArgumentParser()
    p.add_argument('--reset', action='store_true',
                   help='reset the db entirely')
    p.add_argument('--verbose', action='store_true',
                   help='print the values of the db after a set attempt')
    return p.parse_args()


if __name__ == '__main__':
    args = get_args()
    app = create_app()
    with app.test_request_context():
        # Transactions are committed when the request is __exit__ed
        init_db(reset=args.reset, verbose=args.verbose)
