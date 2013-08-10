from equanimity.zeo import Zeo
import transaction

from equanimity.battle import * 
#from stores.store import get_persisted
from copy import deepcopy

zeo = Zeo()
world = zeo.root
f = world['Fields']['(0, 0)']
atkr_name, atksquad = f.attackerqueue[0] 
defsquad = f.get_defenders()
dfndr = Player(f.owner, squads=[defsquad])
atkr = Player(atkr_name, squads=[atksquad])
f.game = Game(grid=f.grid, defender=dfndr, attacker=atkr)
f._p_changed = 1
transaction.commit()
g = f.game
btl = g.battlefield
