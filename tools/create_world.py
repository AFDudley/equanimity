"""creates the World object and populates it with fields. VERY DESTRUCTIVE."""
from equanimity.const import *
from equanimity.stone import Stone
from equanimity.world import Player, World
import transaction

w = World()
wr = w.root
try:
    w.create()

    #player stuff
    w.add_player(Player('dfndr', 'dfndr'))
    w.add_player(Player('atkr', 'atkr'))

    w.award_field('World', '(0, 0)', 'dfndr')
    w.award_field('World', '(0, 1)', 'atkr')

    #Fields are automatically populated with Ice mins.
    #below we create attacking Fire mins.
    #get fields
    af = wr['Players']['atkr'].Fields['(0, 1)']
    df = wr['Players']['dfndr'].Fields['(0, 0)']
    #get stronghold.
    afs = af.stronghold

    #put Fire min stones into stronghold. err, not taking food into account correctly.
    afs.silo.imbue_list([Stone((16,32,0,16)) for n in xrange(4)])

    #create scients.
    for n in xrange(4): afs.form_scient('Fire', Stone((2,4,0,2)).comp)


    #create weapons.
    for n in WEP_LIST: afs.form_weapon('Fire', Stone().comp, n)

    #create list of last 4 unit_ids
    ln = len(afs.units)
    uids = [afs.units[n].id for n in range(ln)[ln - 4:ln]]
    #equip scients.
    for uid in uids: afs.equip_scient(uid, -1) #equip removes weapons from list.
        
    #form squad
    afs.form_squad(uids, 'Fire Attackers')

    #set squad locations
    df.stronghold.set_defender_locs([(6,4), (7,4), (8,4,), (9,4)])
    df.stronghold.apply_defender_locs()
    afs.apply_squad_locs(0, [(6,10), (7,10), (8,10), (9,10)])

    #move squad to attackerqueue
    w.move_squad(af, -1, df)
except:
    raise
    #raise Exception("Pre-existing world not modified.")
