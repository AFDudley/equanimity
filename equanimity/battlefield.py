"""
battlefield.py

Created by AFD on 2013-08-05.
Copyright (c) 2013 A. Frederick Dudley. All rights reserved.
"""
"""contains battlefield objects"""
import random
from math import ceil, sqrt
from datetime import datetime

from const import E, F, I, W
from stone import Stone
from units import Scient, Nescient, Part
from grid import Grid, Tile, Loc, noloc

class Battlefield(object):
    """contains grid, units and the logic for unit damage and movement."""
    def __init__(self, grid=Grid(), defsquad=None, atksquad=None):
        #grid is a tuple of tuples containing tiles
        self.game_id = 0 #?
        self.grid = grid
        self.graveyard = []
        self.defsquad = defsquad
        self.atksquad = atksquad
        self.dmg_queue = {}
        self.squads = (self.defsquad, self.atksquad)
        self.units = self.get_units()
        self.direction = {0:'North', 1:'Northeast', 2:'Southeast', 3:'South', 4:'Southwest', 5:'Northwest'}
        self.ranged = ('Bow',   'Magma',     'Firestorm', 'Forestfire', 'Pyrocumulus')
        self.DOT    = ('Glove', 'Firestorm', 'Icestorm',  'Blizzard',   'Pyrocumulus')
        self.AOE    = ('Wand',  'Avalanche', 'Icestorm',  'Blizzard',   'Permafrost',)
        self.Full   = ('Sword', 'Magma',     'Avalanche', 'Forestfire', 'Permafrost')
        
    def get_units(self):
        """looks in squads, returns all units in squads."""
        #Squads should be made immutable somewhere in Battlefield.
        units = []
        for squad in self.squads:
            if squad != None:
                for unit in squad:
                    units.append(unit)
        return tuple(units)
    
    def on_grid(self, tile):
        """returns True if tile is on grid"""
        if 0 <= tile[0] < self.grid.x:
            if 0 <= tile[1] < self.grid.y:
                return True
            else:
                return False
        else:
            return False
    
    def get_adjacent(self, tile, direction="All"):
        """returns a set of hextiles adjacent to the tile provided, if they are in fact on the grid."""
        direction = direction
        xpos,ypos = tile
        directions = {"East":((xpos + 1, ypos),), "West":((xpos - 1, ypos),),}
        if ypos&1: #sub-optimal
            directions.update({"North":((xpos + 1, ypos - 1),(xpos, ypos - 1)),
                          "South":((xpos + 1, ypos + 1), (xpos, ypos + 1)),
                          "Northeast":((xpos + 1, ypos - 1), (xpos + 1, ypos)),
                          "Southeast":((xpos + 1, ypos + 1), (xpos + 1, ypos)),
                          "Southwest":((xpos, ypos + 1), (xpos - 1, ypos)),
                          "Northwest":((xpos, ypos - 1), (xpos - 1, ypos)),})
        else:
            directions.update({"North":((xpos, ypos - 1),(xpos - 1, ypos - 1)),
                          "South":((xpos, ypos + 1), (xpos - 1, ypos + 1)),
                          "Northeast":((xpos, ypos - 1), (xpos + 1, ypos)),
                          "Southeast":((xpos, ypos + 1), (xpos + 1, ypos)),
                          "Southwest":((xpos - 1, ypos + 1), (xpos - 1, ypos)),
                          "Northwest":((xpos - 1, ypos - 1), (xpos - 1, ypos)),})
        directions["All"] = directions["North"] + directions["East"] + directions["South"] + directions["West"]
        out = []
        for loc in directions[direction]:
            if self.on_grid(loc):
                out.append(loc)
        return set(out)
    
    def make_parts(self, part_locs):
        new_body = {}
        for part in part_locs:
            new_body[part] = Part(None, part_locs[part])
        return new_body
        
    
    def make_body(self, right, direction):
        """makes a nescient body facing direction from right loc"""
        rx, ry = right
        if ry & 1: 
            facing = {'North': {'head':(rx, ry - 1), 'left':(rx - 1, ry), 'tail':(rx, ry + 1)},
                      'South': {'head':(rx + 1, ry + 1), 'left':(rx + 1, ry), 'tail':(rx + 1, ry - 1)},
                      'Northeast': {'head': (rx + 1, ry - 1), 'left':(rx, ry - 1), 'tail':(rx - 1, ry)}, 
                      'Southeast': {'head': (rx + 1, ry), 'left':(rx + 1, ry - 1), 'tail':(rx, ry - 1)}, 
                      'Southwest': {'head':(rx, ry + 1) , 'left':(rx + 1, ry + 1), 'tail':(rx + 1, ry)},
                      'Northwest': {'head': (rx - 1, ry), 'left':(rx, ry + 1), 'tail':(rx + 1, ry + 1)}}
        else:
            facing = {'North': {'head':(rx - 1, ry - 1), 'left':(rx - 1, ry), 'tail':(rx - 1, ry + 1)},
                      'South': {'head':(rx, ry + 1), 'left':(rx + 1, ry), 'tail':(rx, ry - 1)},
                      'Northeast': {'head': (rx, ry - 1), 'left':(rx - 1, ry - 1), 'tail':(rx - 1, ry)}, 
                      'Southeast': {'head': (rx + 1, ry), 'left':(rx, ry - 1), 'tail':(rx - 1, ry - 1)}, 
                      'Southwest': {'head': (rx - 1, ry + 1), 'left':(rx, ry + 1), 'tail':(rx + 1, ry)},
                      'Northwest': {'head': (rx - 1, ry), 'left':(rx - 1, ry + 1), 'tail':(rx, ry + 1)}}
        
        part_locs = facing[direction]
        part_locs.update({'right':(rx, ry)})
        return self.make_parts(part_locs)
    
    def body_on_grid(self, body):
        """checks if a body is on_grid"""
        body = body
        for part in body:
            if not self.on_grid(body[part].location):
                return False
            else: return True
    
    def can_move_nescient(self, body, nescient):
        """checks if nescient can move to body."""
        for part in body:
            xdestp, ydestp = body[part].location
            if self.grid[xdestp][ydestp].contents != None:
                if self.grid[xdestp][ydestp].contents not in nescient.body.values():
                    if type(self.grid[xdestp][ydestp].contents) != type(Stone()):
                        return False
                    else: pass
                else: pass
            else: pass
        return True
    
    def move_nescient(self, new_body, nescient):
        """places new_body on grid, place body in nescient."""
        new_body = new_body
        for part in new_body:
            xdestp, ydestp = new_body[part].location
            if self.grid[xdestp][ydestp].contents != None:
                if self.grid[xdestp][ydestp].contents not in nescient.body.values():
                    if type(self.grid[xdestp][ydestp].contents) != type(Stone()):
                        raise Exception("Not enough space to move Nescient.")
                    else:
                        self.grid[xdestp][ydestp].contents = new_body[part]
                else:
                    pass
            else:
                self.grid[xdestp][ydestp].contents = new_body[part]
        nescient.take_body(new_body)
        nescient.location = nescient.body['right'].location
        return True
    
    def place_nescient(self, nescient, dest):
        """place a nescient so that its right is at dest."""
        facing = nescient.facing
        if facing == None:
            facing = 'North'
        xdest, ydest = dest = dest
        if self.on_grid(dest): #is dest on grid?
            new_body = self.make_body(dest, facing)
            if self.body_on_grid(new_body):
                nescient.facing = facing #ick.
                return self.move_nescient(new_body, nescient)
            else:
                raise Exception("A body part is not on grid.")
        else:
            raise Exception("Destination %s is not on grid" %dest)
    
    def get_rotations(self, nescient):
        """returns list of directions nescient can rotate."""
        drctns = []
        sntcrd = dict(zip(self.direction.values(), self.direction.keys()))
        nbdr = nescient.body['right'].location
        for direction in sntcrd:
            if self.can_move_nescient(self.make_body(nbdr, direction), nescient):
                drctns.append(direction) #might want to return body as well.
        return drctns
    
    def rotate(self, nescient, direction):
        """rotates Nescient so that head is facing direction"""
        nes = nescient
        new_body = self.make_body(nes.body['right'].location, direction)
        if self.body_on_grid(new_body):
            if self.move_nescient(new_body, nescient):
                nescient.facing = direction
                return True
            else:
                raise Exception("Move Failed.")
        else:
            raise Exception('nescient cannot rotate to that direction')
    
    def make_triangle(self, location, distance, pointing):
        """generates an equilateral triangle pattern with 'location' at one
        point. The other two points are 'distance' away from 'location'
        toward 'pointing'. Returns a set of coords"""
        location  = location
        dist = distance
        pointing = pointing
        triangle = []
        head = self.get_adjacent(location, pointing) #get first two points.
        cols = 1 #maintain dist = 1 behavior.
        while cols != dist:
            triangle += list(head)
            temp_head = head
            head = set()
            for loc in temp_head:
                head |= self.get_adjacent(loc, pointing)
            cols += 1
        return triangle
    
    def map_to_grid(self, location, weapon):
        """returns tiles within range of location using weapon. called in hex_view.py"""
        weapon = weapon
        xpos, ypos = location = location
        if weapon.type in (self.ranged + self.AOE):
            move = 4
            no_hit = self.make_range(location, move)
            hit    = self.make_range(location, 2*move)
            return hit - no_hit
        else:
            return self.get_adjacent(location)
    
    def make_range(self, location, distance):
        """generates a list of tiles within distance of location."""
        location = location
        dist = distance
        tiles = []
        #so far from optimal
        tiles.append(self.get_adjacent(location))
        while len(tiles) < dist:
            new = set()
            for tile in tiles[-1]:
                new |= self.get_adjacent(tile)
            tiles.append(new)
        group = set()
        for x in tiles: group |= x
        return group
    
    def place_object(self, obj, dest):
        """places an object on a tile."""
        try:
            if self.on_grid(dest):
                xpos, ypos = dest
            else:
                raise Exception("Tile %s is off grid" %dest)
        except TypeError:
            pass
            
        if isinstance(obj, Scient):
            if (obj.location == noloc) or (obj.location == None):
                if self.grid[xpos][ypos].contents == None:
                    self.grid[xpos][ypos].contents = obj
                    obj.location = Loc(xpos, ypos)
                    self.dmg_queue[obj] = [] #append unit to dmg_queue
                    return True
                    
                elif unit.location == Loc(xpos, ypos):
                    raise Exception("This unit is already on (%s,%s)" %(xpos, ypos))
                    
                elif self.grid[xpos][ypos].contents != None:
                    raise Exception("(%s, %s) is not empty" %(xpos, ypos))
            else:
                return self.move_scient(obj.location, dest)
            
        elif isinstance(obj, Nescient):
            return self.place_nescient(obj, dest)
        elif isinstance(obj, Stone):
            pass
        else:
            raise TypeError("obj is not a game item.")
    
    def move_scient(self, src, dest):
        """move unit from src tile to dest tile"""
        if self.on_grid(src):
            xsrc, ysrc = src
        else:
            raise Exception("Source %s is off grid" %src)
        
        if self.on_grid(dest):
            xdest, ydest = dest
        else:
            raise Exception("Destination %s is off grid" %dest)
        
        if self.grid[xsrc][ysrc].contents:
            if not self.grid[xdest][ydest].contents:
                move = self.grid[xsrc][ysrc].contents.move
                if dest in self.make_range(src, move):
                    self.grid[xdest][ydest].contents = \
                    self.grid[xsrc][ysrc].contents
                    self.grid[xdest][ydest].contents.location = Loc(xdest, ydest)
                    self.grid[xsrc][ysrc].contents = None
                    return True
                else:
                    raise Exception("tried moving more than %s tiles" %move)
            else:
                raise Exception("There is already something at %s" %str(dest))
        else:
            raise Exception("There is nothing at %s" %str(src))
    
    def place_scient(self, unit, tile):
        """Places unit at tile, if already on grid, move_scient is called"""
        if self.on_grid(tile):
            xpos, ypos = tile
        else:
            raise Exception("Tile %s is off grid" %tile)
        
        if unit.location == noloc:
            if self.grid[xpos][ypos].contents == None:
                self.grid[xpos][ypos].contents = unit
                unit.location = Loc(xpos, ypos)
                self.dmg_queue[unit] = [] #append unit to dmg_queue
                return True
            
            elif unit.location == Loc(xpos, ypos):
                raise Exception("This unit is already on (%s,%s)" %(xpos, ypos))
            
            elif self.grid[xpos][ypos].contents != None:
                raise Exception("(%s, %s) is not empty" %(xpos, ypos))
        else:
            return self.move_scient(unit.location, tile)
    
    def find_units(self):
        """returns a list of units in grid."""
        lst = []
        for x in range(len(self.grid)): #maybe using .x and .y would be faster?
            for y in range(len(self.grid[x])):
                if self.grid[x][y].contents:
                    lst.append((x, y)) #maybe this should be a loc?
        return lst
    
    def rand_place_scient(self, unit):
        """Randomly place a unit on the grid."""
        #readable?
        inset = 0 #place units in a smaller area, for testing.
        def Randpos():
            """returns a random position in grid."""
            return (random.randint(0, ((self.grid.x - 1) - inset)),
            random.randint(0, ((self.grid.y - 1) - inset)))
        if len(self.find_units()) == (self.grid.x * self.grid.y):
            raise Exception("Grid is full")
        else:
            while unit.location == noloc:
                try:
                    self.place_scient(unit, Randpos())
                    break
                except Exception:
                    pass
    
    def rand_place_squad(self, squad):
        """place the units in a squad randomly on the battlefield"""
        for unit in range(len(squad)):
            self.rand_place_scient(squad[unit])
    
    def flush_units(self):
        """
        remove all units from grid, returns number of units flushed,
        does not put them in the graveyard. (for testing)
        """
        #maybe find_unit should be used here...
        num = 0
        for x in range(len(self.grid)):
            for y in range(len(self.grid[x])):
                if self.grid[x][y].contents:
                    self.grid[x][y].contents.location = noloc
                    self.grid[x][y].contents = None
                    num += 1
        return num
    
    #Attack/Damage stuff
    def dmg(self, atkr, defdr):
        """Calculates the damage of an attack"""
        dloc = defdr.location
        damage_dealt = {E: 0, F: 0, I: 0, W: 0}
        if self.on_grid(dloc):
            if atkr.weapon.kind == 'p':
                for element in damage_dealt:
                    dmg = (atkr.p + atkr.patk + (2 * atkr.comp[element]) +
                    atkr.weapon.comp[element]) - (defdr.p + defdr.pdef +
                    (2 * defdr.comp[element]) + self.grid[dloc[0]][dloc[1]].comp[element])
                    dmg = max(dmg, 0)
                    damage_dealt[element] = dmg
                damage = sum(damage_dealt.values())
                return damage
            else:
                for element in damage_dealt:
                    dmg = (atkr.m + atkr.matk + (2 * atkr.comp[element]) +
                    atkr.weapon.comp[element]) - (defdr.m + defdr.mdef +
                    (2 * defdr.comp[element]) + self.grid[dloc[0]][dloc[1]].comp[element])
                    dmg = max(dmg, 0)
                    damage_dealt[element] = dmg
                
                damage = sum(damage_dealt.values())
                if atkr.element == defdr.element:
                    return 0 - damage
                else:
                    return damage
        else:
            raise Exception("Defender is off grid")
    
    def make_distances(self, src, dest, direction='all'):
        ax,ay = src
        dx,dy = dest
        xdist = abs(dx - ax)
        ydist = abs(dy - ay)
        zdist = xdist + ydist/2 + 1
        ranges = {}
        for index in range(6):
            ranges[index] = zdist
        
        ranges.update({0:ydist + 1, 3:ydist + 1,})
        if ay & 1:
            if not dy & 1:
                ranges.update({4:zdist + 1, 5:zdist + 1,})
        else:
            if dy & 1:
                ranges.update({1:zdist + 1, 2:zdist + 1,})
        if direction == 'all':
            return ranges
        else:
            return ranges[direction]
        
    def maxes(self, src):
        '''NOTE: Currently, AOE weapons can hit every tile on the grid so this is
                 really quite moot.
                 
                 At some point LOS style blasting might be added at which
                 point this would be needed.
        '''
        #sub-optimal should check ay % 1 and change the + 1 and + 2 accordingly.
        ax, ay = src
        maxes = {
                0:ay + 1,
                1:(self.grid.x - ax) + ay/2,
                2:(self.grid.x - ax) + (self.grid.y - ay)/2, 
                3:self.grid.y - ay,
                4:ax + (self.grid.y - ay)/2 + 1,
                5: ax + ay/2 + 2,
                }
        return maxes
    
    def calc_AOE(self, atkr, target):
        """Returns the AOE of a spell. Called once in hex_view.py"""
        #Optimize. Currently makes a triangle only to discard 7/8ths of it.
        xpos, ypos = aloc = atkr.location
        tloc = Loc._make(target)
        dists = self.make_distances(aloc, tloc)
        maxes = self.maxes(aloc)
        for i in self.direction:
            pat = self.make_triangle(aloc, maxes[i], self.direction[i])
            if tloc in pat:
                pat_ = self.make_triangle(aloc, dists[i], self.direction[i])
                new_pat = []
                for tile in pat_:
                    if self.on_grid(tile):
                        if dists[i] == self.make_distances(aloc, tile, i):
                            new_pat.append(tile)
                new_pat = set(new_pat)
                return new_pat
    
    def calc_ranged(self, atkr, target):
        """UGH"""
        #use something like get_rotations to target 4 tiles at a time.
        #maybe it should magically hit 4 contigious tiles?
        pass
    
    def calc_damage(self, atkr, defdr):
        """Calcuate damage delt to defdr from atkr. Also calculates the damage of
        all units within a blast range. if weapon has a AOE list of
        [[target, dmg]] is returned. otherwise just (target, dmg) is returned"""
        weapon = atkr.weapon
        aloc = atkr.location
        dloc = defdr.location
        dmg_lst = []
        in_range = self.map_to_grid(aloc, weapon)
        if not(dloc in in_range):
            raise Exception( \
            "Defender's location: %s is outside of attacker's range" %str(dloc))
        else:
            #calculate how many units will be damaged.
            if weapon.type in self.AOE:
                pat = self.calc_AOE(atkr, dloc)
                targets = list(set(self.find_units()) & set(pat))
                area = len(pat)
                for t in targets:
                    defdr = self.grid[t[0]][t[1]].contents
                    temp_dmg = self.dmg(atkr, defdr)
                    if temp_dmg != 0:
                        #currently the only non-full, non-DOT AOE weapon
                        if weapon.type != 'Wand':
                            dmg_lst.append((defdr, temp_dmg))
                        else:
                            temp_dmg /= area
                            if temp_dmg != 0:
                                dmg_lst.append((defdr, temp_dmg))
                    else:
                        pass # no damage was dealt, don't append anything.
                
            elif weapon.type in self.ranged:
                #this is a placeholder until calc_ranged is written.
                dmg_lst.append((defdr, self.dmg(atkr, defdr) / 4))
            else: #attack is only hitting one unit.
                dmg_lst.append((defdr, self.dmg(atkr, defdr)))
            
            if weapon.type in self.DOT:
                dmg_lst = [(t[0], t[1] / weapon.time) for t in dmg_lst]
            
            if len(dmg_lst):
                return dmg_lst
            else:
                return None
    
    def apply_dmg(self, target, damage):
        """applies damage to target, called by attack() and
        apply_queued() returns damage applied"""
        if damage >= target.hp:
            try:
                self.bury(target)
                return "Dead."
                #return target.hp
            except:
                raise Exception("STOP BEING GREEDY.")
        else:
            target.hp -= damage
            return damage
    
    def bury(self, unit):
        """moves unit to graveyard"""
        x,y = unit.location
        unit.hp = 0
        unit.DOD = datetime.utcnow()
        self.grid[x][y].contents = None
        unit.location = Loc(-1,-1)
        del self.dmg_queue[unit]
        self.graveyard.append(unit)
        return True
    
    def attack(self, atkr, target):
        """calls calc_damage, applies result, Handles death."""
        defdr = self.grid[target[0]][target[1]].contents
        if isinstance(defdr, Part):
            defdr = defdr.nescient
        dmg = self.calc_damage(atkr, defdr)
        if dmg != None:
            defdr_HPs = []
            if atkr.weapon.type in self.DOT:
                for i in dmg:
                    if i[0].hp > 0:
                        self.dmg_queue[defdr].append([i[1], (atkr.weapon.time - 1)])
                        defdr_HPs.append([i[0], self.apply_dmg(i[0], i[1])])
            else:
                for i in dmg:
                    if i[0].hp > 0:
                        defdr_HPs.append([i[0], self.apply_dmg(i[0], i[1])])
            return defdr_HPs
        else: #no damage
            return []    
    
    def get_dmg_queue(self):
        """returns a copy of the dmg_queue."""
        new_dict = {}
        for (key, value) in self.dmg_queue.items():
            new_lst = []
            for lst in value:
                new_lst.append(tuple(lst))
                new_dict[key] = new_lst
        return new_dict
    
    def apply_queued(self):
        """applies damage to targets stored in dmg_queue"""
        defdr_HPs = []
        for i in self.dmg_queue.keys():
            udmg = []
            for dmg_lst in reversed(xrange(len(self.dmg_queue[i]))):
                udmg.append(self.dmg_queue[i][dmg_lst][0])
                self.dmg_queue[i][dmg_lst][1] -= 1
                if self.dmg_queue[i][dmg_lst][1] == 0:
                    del self.dmg_queue[i][dmg_lst]
            
            udmg = sum(udmg)
            if udmg != 0:
                defdr_HPs.append([i, self.apply_dmg(i, udmg)])
        return defdr_HPs
    
