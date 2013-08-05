"""
weapons.py

Created by AFD on 2013-08-05.
Copyright (c) 2013 A. Frederick Dudley. All rights reserved.
"""
from stone import Stone
class Weapon(Stone):
    """Scients Equip weapons to do damage"""
    def __init__(self, element, comp, wep_type, kind=None):
        #this should return the correct weapon based on . (?)
        Stone.__init__(self, comp)
        self.type = wep_type
        self.element = element
        self.kind = kind

    def map_to_grid(self, origin, grid_size):
        #TODO move to battlefield
        """maps pattern to grid centered on origin.
        Returns list of tiles on grid. (Lots of room for optimization)"""
        orix,oriy = origin
        tiles = []
        if self.type != 'Wand':
            if self.type == 'Bow':
                no_hit = 4 #the scient move value
                mini = -(2 * no_hit)
                maxi = -mini + 1
                dist = range(mini,maxi)
                attack_pattern = []
                #???
                [[attack_pattern.append((x,y)) for y in dist if (no_hit < (abs(x) + abs(y)) < maxi) ] for x in dist]
            else:
                attack_pattern = [(0,-1),(1,0),(0,1),(-1,0),(-1,-1),(-1,1),(1,1),(1,-1)]
            
            for i in attack_pattern:
                x,y = (i[0] + origin[0]),(i[1] + origin[1])
                if 0 <= x < grid_size[0]:
                    if 0 <= y < grid_size[1]:
                        tiles.append((x,y))
            return tiles
        else:
            def make_pattern(self, origin, distance, pointing):
                """generates a pattern based on an origin, distance, and
                direction. Returns a set of coords"""
                #TODO: use inversion to create Wand/Ice attack pattern.
                #needs lots o checking
                src = origin
                sid = 2 * distance
                pattern = []
                tiles = []
                for i in xrange(sid): #generate pattern based on distance from origin
                    if i % 2:
                        in_range = xrange(-(i/2),((i/2)+1))
                        #rotate pattern based on direction
                        for j in xrange(len(in_range)):
                            if pointing == 'North':
                                pattern.append((src[0] + in_range[j], (src[1] - (1 +(i/2)))))
                            elif pointing =='South':
                                pattern.append((src[0] + in_range[j], (src[1] + (1 +(i/2)))))
                            elif pointing =='East':
                                pattern.append((src[0] +  (1 +(i/2)), (src[1] - in_range[j])))
                            elif pointing =='West':
                                pattern.append((src[0] -  (1 +(i/2)), (src[1] - in_range[j])))
                
                return pattern
            direction = {0:'West', 1:'North', 2:'East', 3:'South'}
            maxes = (origin[0], origin[1], (grid_size[0] - 1 - origin[0]), \
            (grid_size[1] - 1 - origin[1]),)
            tiles = []
            for i in direction:
                for j in  self.make_pattern(origin, maxes[i], direction[i]):
                    if 0 <= j[0] < grid_size[0]:
                        if 0 <= j[1] < grid_size[1]:
                            tiles.append(j)
            return tiles

class Sword(Weapon):
    """Close range physial weapon"""
    def __init__(self, element, comp):
        Weapon.__init__(self, element, comp, 'Sword')
        self.kind = 'p'

class Bow(Weapon):
    """Long range physical weapon"""
    def __init__(self, element, comp):
        Weapon.__init__(self, element, comp, 'Bow')
        self.kind = 'p'

class Wand(Weapon):
    """Long range magical weapon"""
    def __init__(self, element, comp):
        Weapon.__init__(self, element, comp, 'Wand')
        self.kind = 'm'
    
    def make_pattern(self, origin, distance, pointing):
        """generates a pattern based on an origin, distance, and
        direction. Returns a set of coords"""
        #TODO: use inversion to create wand attack pattern.
        #needs lots o checking
        src = origin
        sid = 2 * distance
        pattern = []
        tiles = []
        for i in xrange(sid): #generate pattern based on distance from origin
            if i % 2:
                in_range = xrange(-(i/2),((i/2)+1))
                #rotate pattern based on direction
                for j in xrange(len(in_range)):
                    if pointing == 'North':
                        pattern.append((src[0] + in_range[j], (src[1] -
                                       (1 +(i/2)))))
                    elif pointing =='South':
                        pattern.append((src[0] + in_range[j], (src[1] +
                                       (1 +(i/2)))))
                    elif pointing =='East':
                        pattern.append((src[0] +  (1 +(i/2)), (src[1] -
                                        in_range[j])))
                    elif pointing =='West':
                        pattern.append((src[0] -  (1 +(i/2)), (src[1] -
                                        in_range[j])))
        
        return pattern

class Glove(Weapon):
    """Close range magical weapon"""
    def __init__(self, element, comp):
        Weapon.__init__(self, element, comp, 'Glove')
        self.kind = 'm'
        self.time = 3

