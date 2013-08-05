"""
stone.py

Created by AFD on 2013-08-05.
Copyright (c) 2013 A. Frederick Dudley. All rights reserved.
"""
from collections import namedtuple, Mapping
from persistent import Persistent
from const import ELEMENTS, E, F, I, W

class Stone(Persistent, Mapping):
    """ugh."""
    def __init__(self, comp=None):
        #Limit should be overwritten by classes that inherit from Stone.
        self.limit = {'Earth':255, 'Fire': 255, 'Ice': 255, 'Wind': 255}
        self.comp = {'Earth': 0, 'Fire': 0, 'Ice': 0, 'Wind': 0}
        #self.id = randint(1000000000, 2**32)
        if isinstance(comp, Stone):
            self.comp = comp.comp
        if comp == None:
            comp = self.comp
        else:
            try:
                iter(comp)
                if sorted(self.comp) == sorted(comp):
                    self.comp = dict(comp)
                else:
                    if len(comp) == 4 or len(comp) == 0:
                        for element in range(4):
                            if type(comp[element]) == type(1):
                                if 0 <= comp[element] <= self.limit[ELEMENTS[element]]:
                                    self.comp[ELEMENTS[element]] = comp[element]
                                else:
                                    raise AttributeError
                            else:
                                raise TypeError
                    else:
                        raise ValueError
            except TypeError:
                raise
        
    def __iter__(self):
         return iter(self.comp)
    def __contains__(self, value):
         return value in self.comp
    def __getitem__(self,key):
        return self.comp[key]
    def __setitem__(self,key,value):
        if value <= self.limit[key]:
            self.comp[key] = value
        else:
            raise AttributeError("Tried setting %s beyond its limit of %s"  %(key, str(self.limit[key])))
    def __len__(self):
         return len(self.comp)

    """
    __hash__ and __cmp__ are hacks to get around scients being mutable.
    I think the answer is to actually make stones immutable and
    have imbue return a different stone.
    """

    def __hash__(self):
        return id(self)
    
    def imbue(self, stone):
        """adds the values of stone.comp to self.comp up to self.limit.
           leaves any remaining point in stone and returns stone."""
        if isinstance(stone, Stone):
            for s in ELEMENTS:
                if (self.comp[s] + stone[s]) <= self.limit[s]:
                    self.comp[s] += stone[s]
                    stone[s] = 0
                else:
                    r = self.limit[s] - self.comp[s]
                    stone[s] -= r
                    self.comp[s] += r
            
            if stone.value() == 0:
                del stone
                return
            else:
                return stone
        else:
            raise TypeError("Stone must be a stone.")
    
    def split(self, comp):
        """subtracts comp from self, returns new stone"""
        if sum(comp.values()) > self.value(): # > instead of >= for the silo case.
            raise ValueError("Sum of comp must be less than value of stone.")
        else:
            s = Stone()
            for e in ELEMENTS:
                if comp[e] > self.comp[e]:
                    raise ValueError("comp[%s] cannot be greater than "
                                     "stone[%s]." %(e, e))
                else:
                    self.comp[e] -= comp[e]
                    s[e] = comp[e]
        return s
        
    def tup(self):
        tup = ()
        for key in sorted(self.comp):
            tup += (self.comp[key],)
        return tup
        
    def value(self):
        return sum(self.comp.values())
