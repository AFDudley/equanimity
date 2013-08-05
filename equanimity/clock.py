"""
clock.py

Created by AFD on 2013-08-05.
Copyright (c) 2013 A. Frederick Dudley. All rights reserved.
"""
import sys
from datetime import datetime, timedelta
import json
import copy

from zeo import Zeo

def now():
    return datetime.utcnow()

class Clock():
    """World time related functions."""
    def get_name(self, uot):
        if uot == 'day':
            num = self.uot_num['day'] % 6
        elif uot == 'week':
            num = self.uot_num['week'] % 5
        elif uot == 'month':
            num = self.uot_num['month'] % 3
        elif uot == 'season':
            num = self.uot_num['season'] % 4
            if num == 0: return "Earth"
            elif num == 1: return "Fire"
            elif num == 2: return "Ice"
            elif num == 3: return "Wind"
        else:
            return

        if num == 0: return "One"
        elif num == 1: return "Two"
        elif num == 2: return "Three"
        elif num == 3: return "Four"
        elif num == 4: return "Five"
        elif num == 5: return "Six"
    
    def update(self):
        since_dob = (now() - self.DOB).total_seconds()
        dur = self.duration
        uot_num = {}
        uot_name = {}
        for uot in dur.keys():
            num = int(since_dob / dur[uot])
            uot_num[uot] = num
            uot_name[uot] = self.get_name(uot)
        self.uot_num = uot_num
        self.uot_name = uot_name
        
    def __init__(self, addr=('localhost', 9100)):
        world = Zeo(addr)
        self.DOB = copy.deepcopy(world.root['DOB'])
        self.duration = {'day': copy.deepcopy(world.root['dayLength'])}
        self.duration['week'] = self.duration['day'] * 6
        self.duration['month'] = self.duration['week'] * 5
        self.duration['season'] = self.duration['month'] * 3
        self.duration['year'] = self.duration['season'] * 4
        self.duration['generation'] = self.duration['year'] * 14
        self.uot_num = {'day': 0, 'week': 0, 'month': 0, 'season': 0, 'year': 0, 'generation': 0}
        self.uot_name = {'day': 'one', 'week': 'one', 'month': 'one', 'season': 'Earth', 'year': 'one', 'generation': 'one'}
        #Get uot_num and uot_name correct.
        self.update()
        world.db.close()
        
    def since_dob(self, uot=None):
        """Returns total seconds since DOB in game Units of Time. or seconds."""
        if uot == None:
            return (now() - self.DOB).total_seconds()
        else:
            self.update()
            return self.uot_num[uot]

    def get_delta(self, timedelta, uot):
        """takes a timedelta and returns delta in game UoT."""
        return timedelta.total_seconds() / self.duration[uot]
        
    def get_time(self, uot=None):
        self.update()
        output = ""
        if not uot:
            output += "Day: %s" %self.uot_name['day'] + "\n"
            output += "Week: %s" %self.uot_name['week'] + "\n"
            output += "Month: %s" %self.uot_name['month'] + "\n"
            output += "Season: %s" %self.uot_name['season'] + "\n"
            output += "Year: %s" %self.uot_name['year'] + "\n"
            output += "Generation: %s" %self.uot_name['generation'] + "\n"
        else:
            return self.uot_name[uot]
        return output
            
