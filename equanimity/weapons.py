"""
weapons.py

Created by AFD on 2013-08-05.
Copyright (c) 2013 A. Frederick Dudley. All rights reserved.
"""
from stone import Stone


class Weapon(Stone):
    """Scients Equip weapons to do damage"""
    kind = None

    def __init__(self, element, comp, wep_type):
        #this should return the correct weapon based on . (?)
        super(Weapon, self).__init__(comp)
        self.type = wep_type
        self.element = element
        self.stronghold = None
        self.stronghold_pos = None

    def api_view(self):
        return dict(type=self.type, element=self.element,
                    stronghold=getattr(self.stronghold, 'world_coord', None),
                    stronghold_pos=self.stronghold_pos)

    def add_to_stronghold(self, stronghold, pos):
        self.stronghold = stronghold
        self.stronghold_pos = pos

    def remove_from_stronghold(self):
        self.stronghold = None
        self.stronghold_pos = None

    def get_attack_pattern(self):
        return [(0, -1), (1, 0), (0, 1), (-1, 0), (-1, -1), (-1, 1), (1, 1),
                (1, -1)]

    def map_to_grid(self, origin, grid_size):
        #TODO move to battlefield
        """maps pattern to grid centered on origin.
        Returns list of tiles on grid. (Lots of room for optimization)"""
        orix, oriy = origin
        tiles = []
        attack_pattern = self.get_attack_pattern()
        for i in attack_pattern:
            x, y = (i[0] + origin[0]), (i[1] + origin[1])
            if 0 <= x < grid_size[0]:
                if 0 <= y < grid_size[1]:
                    tiles.append((x, y))
        return tiles

    def make_pattern(self, origin, distance, pointing):
        """generates a pattern based on an origin, distance, and
        direction. Returns a set of coords"""
        #TODO: use inversion to create Wand/Ice attack pattern.
        #needs lots o checking
        src = origin
        sid = 2 * distance
        pattern = []
        #tiles = []
        for i in xrange(sid):  # generate pattern based on distance from origin
            if not (i % 2):
                continue
            half = i / 2
            in_range = xrange(-half, half + 1)
            #rotate pattern based on direction
            for j in xrange(len(in_range)):
                if pointing == 'North':
                    pattern.append((src[0] + in_range[j],
                                   (src[1] - (1 + half))))
                elif pointing == 'South':
                    pattern.append((src[0] + in_range[j],
                                   (src[1] + (1 + half))))
                elif pointing == 'East':
                    pattern.append((src[0] + (1 + half),
                                   (src[1] - in_range[j])))
                elif pointing == 'West':
                    pattern.append((src[0] - (1 + half),
                                   (src[1] - in_range[j])))
        return pattern


class Sword(Weapon):
    """Close range physial weapon"""
    kind = 'p'

    def __init__(self, element, comp):
        super(Sword, self).__init__(element, comp, 'Sword')


class Bow(Weapon):
    """Long range physical weapon"""
    kind = 'p'

    def __init__(self, element, comp):
        super(Bow, self).__init__(element, comp, 'Bow')

    def get_attack_pattern(self):
        no_hit = 4  # the scient move value
        mini = -(2 * no_hit)
        maxi = -mini + 1
        dist = range(mini, maxi)
        attack_pattern = []
        [[attack_pattern.append((x, y)) for y in dist
          if (no_hit < (abs(x) + abs(y)) < maxi)] for x in dist]
        return attack_pattern


class Wand(Weapon):
    """Long range magical weapon"""
    kind = 'm'

    def __init__(self, element, comp):
        super(Wand, self).__init__(element, comp, 'Wand')

    def get_attack_pattern(self):
        raise UserWarning('Wand doesn\'t use an attack pattern')

    def make_pattern(self, origin, distance, pointing):
        """generates a pattern based on an origin, distance, and
        direction. Returns a set of coords"""
        #TODO: use inversion to create wand attack pattern.
        #needs lots o checking
        src = origin
        sid = 2 * distance
        pattern = []
        #tiles = []
        for i in xrange(sid):  # generate pattern based on distance from origin
            if not (i % 2):
                continue
            half = i / 2
            in_range = xrange(-half, half + 1)
            #rotate pattern based on direction
            for j in xrange(len(in_range)):
                if pointing == 'North':
                    pattern.append((src[0] + in_range[j],
                                   (src[1] - (1 + half))))
                elif pointing == 'South':
                    pattern.append((src[0] + in_range[j],
                                   (src[1] + (1 + half))))
                elif pointing == 'East':
                    pattern.append((src[0] + (1 + half),
                                   (src[1] - in_range[j])))
                elif pointing == 'West':
                    pattern.append((src[0] - (1 + half),
                                   (src[1] - in_range[j])))
        return pattern

    def map_to_grid(self, origin, grid_size):
        direction = {0: 'West', 1: 'North', 2: 'East', 3: 'South'}
        maxes = (origin[0], origin[1], (grid_size[0] - 1 - origin[0]),
                 (grid_size[1] - 1 - origin[1]),)
        tiles = []
        for i in direction:
            for j in self.make_pattern(origin, maxes[i], direction[i]):
                if 0 <= j[0] < grid_size[0]:
                    if 0 <= j[1] < grid_size[1]:
                        tiles.append(j)
        return tiles


class Glove(Weapon):
    """Close range magical weapon"""
    kind = 'm'

    def __init__(self, element, comp):
        super(Glove, self).__init__(element, comp, 'Glove')
        self.time = 3


weapons = dict(Sword=Sword, Bow=Bow, Glove=Glove, Wand=Wand)
