#!/usr/bin/env python

from common import hack_syspath
hack_syspath(__file__)
import argparse
from equanimity.world import init_db
from server import create_app


def get_args():
    p = argparse.ArgumentParser()
    p.add_argument('--reset', help='Reset original world')
    p.add_argument('-v', '--verbose', help='Verbose output')
    p.add_argument('--grid-radius', help='Radius of world and field grids')
    p.add_argument('--square-grid', help='Use a square grid')
    return p.parse_args()


if __name__ == '__main__':
    args = get_args()
    with create_app().test_request_context():
        init_db(reset=args.reset, verbose=args.verbose,
                grid_radius=args.grid_radius, square_grid=args.square_grid)
