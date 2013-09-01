#!/usr/bin/env python

from common import hack_syspath
hack_syspath(__file__)
import argparse
import transaction

"""creates the World object and populates it with fields. VERY DESTRUCTIVE."""
from equanimity.const import WEP_LIST
from equanimity.stone import Stone
from equanimity.player import Player
from equanimity.world import World
from server import create_app
from init_db import init_db

def create_world(force=False):
    init_db(reset=force)
    if force:
        World.erase()
    w = World()
    w.create()

    p = Player.get_by_username('dfndr')
    if p is None:
        p = Player('dfndr', 'dfndr@test.com', 'dfndr')
        p.persist()
    q = Player.get_by_username('atkr')
    if q is None:
        q = Player('atkr', 'atkr@test.com', 'atkr')
        q.persist()
    transaction.commit()

    w.award_field(w.player, (0, 0), p)
    w.award_field(w.player, (0, 1), q)

    # fields are automatically populated with Ice mins.
    # below we create attacking Fire mins.
    # get fields
    df = p.fields[(0, 0)]
    af = q.fields[(0, 1)]
    # get stronghold.
    afs = af.stronghold

    # put Fire min stones into stronghold. err, not taking food into account
    # correctly.
    afs.silo.imbue_list([Stone((16, 32, 0, 16)) for n in xrange(4)])

    # create scients.
    for n in xrange(4):
        afs.form_scient('Fire', Stone((2, 4, 0, 2)).comp)

    # create weapons.
    for n in WEP_LIST:
        afs.form_weapon('Fire', Stone().comp, n)

    # create list of last 4 unit_ids
    ln = len(afs.units)
    uids = [afs.units[n].id for n in range(ln)[ln - 4:ln]]
    # equip scients.
    for uid in uids:
        # equip removes weapons from list.
        afs.equip_scient(uid, -1)

    # form squad
    afs.form_squad(uids, 'Fire Attackers')

    # set squad locations
    df.stronghold.set_defender_locs([(6, 4), (7, 4), (8, 4), (9, 4)])
    df.stronghold.apply_defender_locs()
    afs.apply_squad_locs(0, [(6, 10), (7, 10), (8, 10), (9, 10)])

    # move squad to attackerqueue
    w.move_squad(af, -1, df)


def get_args():
    p = argparse.ArgumentParser()
    p.add_argument('--force', action='store_true',
                   help='Force create a new world')
    return p.parse_args()


if __name__ == '__main__':
    args = get_args()
    with create_app().test_request_context():
        create_world(force=args.force)
