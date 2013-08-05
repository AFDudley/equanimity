"""
world.py

Created by AFD on 2013-08-05.
Copyright (c) 2013 A. Frederick Dudley. All rights reserved.
"""
from datetime import datetime

from ZEO import ClientStorage
from ZODB import DB
import transaction
import persistent
#ZODB needs to log stuff
import logging
logging.basicConfig()

from stone import Stone
from field import Field
from zeo import Zeo
from player import Player

class World(Zeo): #this object needs to be refactored.
    def __init__(self, addr=('localhost', 9100)):
        Zeo.__init__(self, addr)
    
    def make_Fields(self, range_x, range_y):
        """creates all Fields used in a game."""
        #right now the World and the Fields are square, they should both be hexagons.
        wf0 = self.root['Players']['World'].Fields
        wf1 = self.root['Fields']
        for coord_x in xrange(range_x):
            for coord_y in xrange(range_y):
                world_coord = (coord_x, coord_y)
                f = Field(world_coord)
                wf0[str(world_coord)] = f
                wf1[str(world_coord)] = f
                transaction.commit()
        return 
        
    def setup(self, version, x, y):
        self.root['dayLength'] = 240 #length of game day in seconds.
        self.root['resigntime'] = 21600#amount of time in seconds before attacker is forced to resign.
        self.root['maxduration'] = 5040 #in gametime days (5040 is one generation, two weeks real-time)
        self.root['version'] = version
        self.root['x'] = x
        self.root['y'] = y
        self.root['DOB'] = datetime.utcnow()
        #Fields should be a frozendict
        #http://stackoverflow.com/questions/2703599/what-would-be-a-frozen-dict
        self.root['Fields']  = persistent.mapping.PersistentMapping()
        self.root['Players'] = persistent.mapping.PersistentMapping()
        self.player = Player('World', None)
        self.root['Players']['World'] = self.player
        return transaction.commit()
        
    def create(self, version=0.0, x=2, y=2):
        #there should be a more elegant way of doing this.
        try: #If the world version is the same, do nothing.
            if self.root['version'] == version:
                return Exception("The ZODB already contains a world of that version.")
            else:
                pass
        except:
            pass
        self.setup(version, x, y)
        self.make_Fields(self.root['x'], self.root['y'])
        return
        
    def add_player(self, player):
        if not(player.username in self.root.keys()):
            self.root['Players'][player.username] = player
            self.root._p_changed = 1
            return transaction.commit()
        else:
            raise Exception("A player with that name is already registered, "
                             "use another name.")
    
    def delete_player(self, player):
        """removes a player from the database and returns their fields to
        the world."""
        for field in self.root['Players'][player].Fields.keys():
            self.award_field(player, field, 'World')
        del self.root['Players'][player]
        return transaction.commit()
    
    def set_password(self, player, new_hash): pass
    def set_email(self, player, email): pass
    
    def award_field(self, old_owner, Field_coords, new_owner):
        """Transfers a field from one owner to another."""
        #is this atomic?
        self.root['Players'][new_owner].Fields[str(Field_coords)] = \
        self.root['Players'][old_owner].Fields[str(Field_coords)]
        del self.root['Players'][old_owner].Fields[str(Field_coords)]
        self.root['Players'][new_owner].Fields[str(Field_coords)].owner =\
        new_owner
        return transaction.commit()
    
    def move_squad(self, src, squad_num, dest):
        """Moves a squad from a stronghold to a queue."""
        #src and dest are both Fields
        #TODO: check for adjacency.
        squad = src.stronghold.squads[squad_num]
        dest.attackerqueue.append((src.owner, squad))
        src.stronghold.remove_squad(squad_num)
        return transaction.commit()
    
    def process_action(self, action):
        pass
