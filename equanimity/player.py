"""
player.py

Created by AFD on 2013-08-05.
Copyright (c) 2013 A. Frederick Dudley. All rights reserved.
"""
import persistent

class Player(persistent.Persistent):
    """Object that contains player infomration."""
    def __init__(self, username, password=None, squads=None):
        persistent.Persistent.__init__(self)
        self.username = username
        self.email = None
        #NOT SECURE!
        if password != None:
            self.password = password
        else:
            self.password = None
        self.squads  = squads
        self.Fields  = persistent.mapping.PersistentMapping()
        self.cookie   = None
        self.roads    = None
        self.treaties = None
    
