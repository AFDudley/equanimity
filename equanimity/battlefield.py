"""
battlefield.py

Created by AFD on 2013-08-05.
Copyright (c) 2013 A. Frederick Dudley. All rights reserved.
"""
"""contains battlefield objects"""
import random
from datetime import datetime

from stone import Stone, Composition
from units import Scient, Nescient, Part
from grid import Grid, Loc, noloc


"""
Refactoring notes:
Grid should not be modified directly, should be a call to a Grid method
Replace ValueError with a custom exception
"""


class Battlefield(object):
    """contains grid, units and the logic for unit damage and movement."""
    def __init__(self, grid=None, defsquad=None, atksquad=None):
        if grid is None:
            grid = Grid()
        # grid is a tuple of tuples containing tiles
        self.game_id = 0  # ?
        self.grid = grid
        self.graveyard = []
        self.defsquad = defsquad
        self.atksquad = atksquad
        self.dmg_queue = {}
        self.squads = (self.defsquad, self.atksquad)
        self.units = self.get_units()
        self.direction = {
            0: 'North',
            1: 'Northeast',
            2: 'Southeast',
            3: 'South',
            4: 'Southwest',
            5: 'Northwest'
        }
        self.ranged = ('Bow', 'Magma', 'Firestorm', 'Forestfire',
                       'Pyrocumulus')
        self.DOT = ('Glove', 'Firestorm', 'Icestorm', 'Blizzard',
                    'Pyrocumulus')
        self.AOE = ('Wand', 'Avalanche', 'Icestorm', 'Blizzard', 'Permafrost')
        self.Full = ('Sword', 'Magma', 'Avalanche', 'Forestfire', 'Permafrost')

    def get_units(self):
        """looks in squads, returns all units in squads."""
        #Squads should be made immutable somewhere in Battlefield.
        units = []
        for squad in self.squads:
            if squad is not None:
                for unit in squad:
                    units.append(unit)
        return tuple(units)

    def on_grid(self, tile):
        # TODO (steve) -- HEX TILE WORK
        """returns True if tile is on grid"""
        return self.grid.in_bounds(tile)

    def get_adjacent(self, tile, direction="All"):
        # TODO (steve) -- HEX TILE WORK
        """returns a set of hextiles adjacent to the tile provided,
        if they are in fact on the grid."""
        direction = direction
        xpos, ypos = tile
        directions = {"East": ((xpos + 1, ypos),),
                      "West": ((xpos - 1, ypos),)}
        if ypos & 1:  # sub-optimal
            directions.update({
                "North": ((xpos + 1, ypos - 1), (xpos, ypos - 1)),
                "South": ((xpos + 1, ypos + 1), (xpos, ypos + 1)),
                "Northeast": ((xpos + 1, ypos - 1), (xpos + 1, ypos)),
                "Southeast": ((xpos + 1, ypos + 1), (xpos + 1, ypos)),
                "Southwest": ((xpos, ypos + 1), (xpos - 1, ypos)),
                "Northwest": ((xpos, ypos - 1), (xpos - 1, ypos)),
            })
        else:
            directions.update({
                "North": ((xpos, ypos - 1), (xpos - 1, ypos - 1)),
                "South": ((xpos, ypos + 1), (xpos - 1, ypos + 1)),
                "Northeast": ((xpos, ypos - 1), (xpos + 1, ypos)),
                "Southeast": ((xpos, ypos + 1), (xpos + 1, ypos)),
                "Southwest": ((xpos - 1, ypos + 1), (xpos - 1, ypos)),
                "Northwest": ((xpos - 1, ypos - 1), (xpos - 1, ypos)),
            })
        directions["All"] = (directions["North"] + directions["East"] +
                             directions["South"] + directions["West"])
        out = []
        for loc in directions[direction]:
            if self.on_grid(loc):
                out.append(loc)
        return set(out)

    def make_parts(self, part_locs):
        new_body = {}
        for name, part in part_locs.iteritems():
            new_body[name] = Part(None, part)
        return new_body

    def make_body(self, right, direction):
        # TODO (steve) -- HEX TILE WORK
        """makes a nescient body facing direction from right loc"""
        rx, ry = right

        def make_dir(head, left, tail):
            return dict(head=head, left=left, tail=tail, right=(rx, ry))

        if ry & 1:
            facing = {
                'North': make_dir((rx, ry - 1), (rx - 1, ry), (rx, ry + 1)),
                'South': make_dir((rx + 1, ry + 1), (rx + 1, ry),
                                  (rx + 1, ry - 1)),
                'Northeast': make_dir((rx + 1, ry - 1), (rx, ry - 1),
                                      (rx - 1, ry)),
                'Southeast': make_dir((rx + 1, ry), (rx + 1, ry - 1),
                                      (rx, ry - 1)),
                'Southwest': make_dir((rx, ry + 1), (rx + 1, ry + 1),
                                      (rx + 1, ry)),
                'Northwest': make_dir((rx - 1, ry), (rx, ry + 1),
                                      (rx + 1, ry + 1))
            }
        else:
            facing = {
                'North': make_dir((rx - 1, ry - 1), (rx - 1, ry),
                                  (rx - 1, ry + 1)),
                'South': make_dir((rx, ry + 1), (rx + 1, ry), (rx, ry - 1)),
                'Northeast': make_dir((rx, ry - 1), (rx - 1, ry - 1),
                                      (rx - 1, ry)),
                'Southeast': make_dir((rx + 1, ry), (rx, ry - 1),
                                      (rx - 1, ry - 1)),
                'Southwest': make_dir((rx - 1, ry + 1), (rx, ry + 1),
                                      (rx + 1, ry)),
                'Northwest': make_dir((rx - 1, ry), (rx - 1, ry + 1),
                                      (rx, ry + 1))
            }
        return self.make_parts(facing[direction])

    def body_on_grid(self, body):
        """checks if a body is on_grid"""
        for part in body.itervalues():
            if self.on_grid(part.location):
                return True
        return False

    def body_within_grid(self, body):
        for part in body.itervalues():
            if not self.on_grid(part.location):
                return False
        return True

    def can_move_nescient(self, body, nescient):
        # TODO (steve) -- HEX TILE WORK. Grid() should have getters
        # instead of [x][y] indexing
        """checks if nescient can move to body."""
        if not self.body_within_grid(body):
            return False
        for part in body.itervalues():
            x, y = part.location
            empty = (self.grid[x][y].contents is None)
            in_self = (self.grid[x][y].contents in nescient.body.itervalues())
            ctype = getattr(self.grid[x][y].contents, '__class__', None)
            is_stone = (ctype == Stone)
            if not empty and not in_self and not is_stone:
                return False
        return True

    def move_nescient(self, new_body, nescient, direction=None):
        # TODO (steve) -- HEX TILE WORK. Grid() should have getters
        # instead of [x][y] indexing
        """places new_body on grid, place body in nescient."""
        if not self.can_move_nescient(new_body, nescient):
            msg = 'Nescient cannot be moved to {0}'
            raise ValueError(msg.format(new_body))
        for part in new_body.itervalues():
            x, y = part.location
            self.grid[x][y].contents = part
        nescient.take_body(new_body)
        nescient.location = nescient.body['right'].location
        if direction is not None:
            nescient.facing = direction
        return True

    def place_nescient(self, nescient, dest):
        """place a nescient so that its right is at dest."""
        facing = nescient.facing
        if facing is None:
            facing = 'North'
        xdest, ydest = dest
        if not self.on_grid(dest):
            raise ValueError('Destination {0} is not on grid'.format(dest))
        new_body = self.make_body(dest, facing)
        self.dmg_queue.setdefault(nescient, [])
        return self.move_nescient(new_body, nescient, direction=facing)

    def get_rotations(self, nescient):
        """returns list of directions nescient can rotate."""
        drctns = []
        nbdr = nescient.body['right'].location
        for direction in self.direction.itervalues():
            body = self.make_body(nbdr, direction)
            if self.can_move_nescient(body, nescient):
                drctns.append(direction)  # might want to return body as well.
        return drctns

    def rotate(self, nescient, direction):
        """rotates Nescient so that head is facing direction"""
        new_body = self.make_body(nescient.body['right'].location, direction)
        return self.move_nescient(new_body, nescient, direction=direction)

    def make_triangle(self, location, distance, pointing):
        """generates an equilateral triangle pattern with 'location' at one
        point. The other two points are 'distance' away from 'location'
        toward 'pointing'. Returns a set of coords"""
        triangle = []
        head = self.get_adjacent(location, pointing)  # get first two points.
        cols = 1  # maintain dist = 1 behavior.
        while cols != distance:
            triangle += list(head)
            temp_head = head
            head = set()
            for loc in temp_head:
                head |= self.get_adjacent(loc, pointing)
            cols += 1
        return triangle

    def map_to_grid(self, location, weapon):
        """returns tiles within range of location using weapon.
        called in hex_view.py"""
        xpos, ypos = location
        if weapon.type in self.ranged or weapon.type in self.AOE:
            move = 4
            no_hit = self.make_range(location, move)
            hit = self.make_range(location, 2 * move)
            return hit - no_hit
        else:
            return self.get_adjacent(location)

    def make_range(self, location, distance):
        """generates a list of tiles within distance of location."""
        location = location
        dist = distance
        tiles = []
        # so far from optimal
        tiles.append(self.get_adjacent(location))
        while len(tiles) < dist:
            new = set()
            for tile in tiles[-1]:
                new |= self.get_adjacent(tile)
            tiles.append(new)
        group = set()
        for x in tiles:
            group |= x
        return group

    def place_object(self, obj, dest):
        """places an object on a tile."""
        if isinstance(obj, Scient):
            return self.place_scient(obj, dest)
        elif isinstance(obj, Nescient):
            return self.place_nescient(obj, dest)
        elif isinstance(obj, Stone):
            # TODO -- should the stone be placed or what?
            raise NotImplementedError('Placing stones is not ready')
        else:
            raise TypeError("{0} is not a game item.".format(obj))

    def move_scient(self, src, dest):
        """move unit from src tile to dest tile"""
        if src == dest:  # No action
            return False
        if not self.on_grid(src):
            raise ValueError("Source {0} is off grid".format(src))
        if not self.on_grid(dest):
            raise ValueError("Destination {0} is off grid".format(dest))

        xsrc, ysrc = src
        xdest, ydest = dest

        if not self.grid[xsrc][ysrc].contents:
            raise ValueError("There is nothing at {0}".format(src))
        if self.grid[xdest][ydest].contents:
            msg = "There is already something at {0}"
            raise ValueError(msg.format(dest))

        move = self.grid[xsrc][ysrc].contents.move
        if dest not in self.make_range(src, move):
            msg = "Tried moving more than {0} tiles"
            raise ValueError(msg.format(move))

        contents = self.grid[xsrc][ysrc].contents
        self.grid[xdest][ydest].contents = contents
        loc = Loc(xdest, ydest)
        self.grid[xdest][ydest].contents.location = loc
        self.grid[xsrc][ysrc].contents = None
        return True

    def place_scient(self, unit, tile):
        """Places unit at tile, if already on grid, move_scient is called"""
        if not self.on_grid(tile):
            raise ValueError("Tile {0} is off grid".format(tile))

        if unit.location != noloc:
            return self.move_scient(unit.location, tile)

        xpos, ypos = tile
        contents = self.grid[xpos][ypos].contents
        if contents is not None:
            raise ValueError("{0} is not empty".format(tile))

        self.grid[xpos][ypos].contents = unit
        unit.location = Loc(xpos, ypos)
        self.dmg_queue.setdefault(unit, [])
        return True

    def find_units(self):
        """returns a list of units in grid."""
        # TODO (steve) -- probably put this on Grid
        units = []
        for x, col in self.grid.iteritems():
            for y, obj in col.iteritems():
                if obj.contents:
                    units.append(Loc(x, y))
        return units

    def rand_place_scient(self, unit):
        """Randomly place a unit on the grid."""
        # readable?
        inset = 0  # place units in a smaller area, for testing.

        def randpos():
            """returns a random position in grid."""
            return (random.randint(0, ((self.grid.x - 1) - inset)),
                    random.randint(0, ((self.grid.y - 1) - inset)))
        # TODO (steve) -- grid.full() method. grid can keep count of what's in
        # it. modify the grid only with accessors
        if len(self.find_units()) == (self.grid.x * self.grid.y):
            raise ValueError("Grid is full")
        while True:
            try:
                return self.place_scient(unit, randpos())
            except ValueError:
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
        for col in self.grid.itervalues():
            for obj in col.itervalues():
                if obj.contents:
                    obj.contents.location = noloc
                    obj.contents = None
                    num += 1
        return num

    #Attack/Damage stuff
    def dmg(self, atkr, defdr):
        """Calculates the damage of an attack"""
        dloc = defdr.location
        damage_dealt = Composition(0)
        if not self.on_grid(dloc):
            raise ValueError("Defender is off grid")

        if atkr.weapon.kind == 'p':
            for element in damage_dealt:
                dmg = ((atkr.p + atkr.patk + (2 * atkr.comp[element]) +
                        atkr.weapon.comp[element]) -
                       (defdr.p + defdr.pdef + (2 * defdr.comp[element]) +
                        self.grid[dloc[0]][dloc[1]].comp[element]))
                dmg = max(dmg, 0)
                damage_dealt[element] = dmg
            damage = sum(damage_dealt.values())
            return damage
        else:
            for element in damage_dealt:
                dmg = ((atkr.m + atkr.matk + (2 * atkr.comp[element]) +
                        atkr.weapon.comp[element]) -
                       (defdr.m + defdr.mdef + (2 * defdr.comp[element]) +
                        self.grid[dloc[0]][dloc[1]].comp[element]))
                dmg = max(dmg, 0)
                damage_dealt[element] = dmg

            damage = sum(damage_dealt.values())
            if atkr.element == defdr.element:
                return 0 - damage
            else:
                return damage

    def make_distances(self, src, dest, direction='all'):
        ax, ay = src
        dx, dy = dest
        xdist = abs(dx - ax)
        ydist = abs(dy - ay)
        zdist = xdist + ydist/2 + 1
        ranges = {}
        for index in xrange(6):
            ranges[index] = zdist

        ranges.update({0: ydist + 1, 3: ydist + 1})
        if ay & 1:
            if not dy & 1:
                ranges.update({4: zdist + 1, 5: zdist + 1})
        else:
            if dy & 1:
                ranges.update({1: zdist + 1, 2: zdist + 1})
        if direction == 'all':
            return ranges
        else:
            return ranges[direction]

    def maxes(self, src):
        """NOTE:
        Currently, AOE weapons can hit every tile on the grid so this is
        really quite moot.

        At some point LOS style blasting might be added at which
        point this would be needed.
        """
        # sub-optimal should check ay % 1 and change the + 1 and + 2
        # accordingly.
        ax, ay = src
        maxes = {
            0: ay + 1,
            1: (self.grid.x - ax) + ay / 2,
            2: (self.grid.x - ax) + (self.grid.y - ay) / 2,
            3: self.grid.y - ay,
            4: ax + (self.grid.y - ay) / 2 + 1,
            5: ax + ay / 2 + 2,
        }
        return maxes

    def calc_AOE(self, atkr, target):
        """Returns the AOE of a spell. Called once in hex_view.py"""
        # Optimize. Currently makes a triangle only to discard 7/8ths of it.
        aloc = atkr.location
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
        return set()

    def calc_ranged(self, atkr, target):
        """UGH"""
        #use something like get_rotations to target 4 tiles at a time.
        #maybe it should magically hit 4 contigious tiles?
        pass

    def calc_damage(self, atkr, defdr, target_loc=None):
        """Calcuate damage delt to defdr from atkr. Also calculates the damage
        of all units within a blast range. if weapon has a AOE list of
        [[target, dmg]] is returned. otherwise just (target, dmg) is
        returned"""
        weapon = atkr.weapon
        aloc = atkr.location
        if hasattr(defdr, 'body'):
            dlocs = [part.location for part in defdr.body.itervalues()]
        else:
            dlocs = [defdr.location]
        dmg_lst = []
        in_range = self.map_to_grid(aloc, weapon)
        if not (set(dlocs) & set(in_range)):
            msg = "Defender's location: {0} is outside of attacker's range"
            raise ValueError(msg.format(dlocs))

        if target_loc is None:
            target_loc = defdr.location

        # calculate how many units will be damaged.
        if weapon.type in self.AOE:
            pat = self.calc_AOE(atkr, target_loc)
            targets = list(set(self.find_units()) & set(pat))
            area = len(pat)
            for t in targets:
                defdr = self.grid[t[0]][t[1]].contents
                temp_dmg = self.dmg(atkr, defdr)
                # currently the only non-full, non-DOT AOE weapon
                if weapon.type == 'Wand':
                    temp_dmg /= area
                dmg_lst.append([defdr, temp_dmg])
        elif weapon.type in self.ranged:
            # this is a placeholder until calc_ranged is written.
            dmg_lst.append([defdr, self.dmg(atkr, defdr) / 4])
        else:  # attack is only hitting one unit.
            dmg_lst.append([defdr, self.dmg(atkr, defdr)])

        if weapon.type in self.DOT:
            dmg_lst = [(t[0], t[1] / weapon.time) for t in dmg_lst]

        return [[unit, dmg] for unit, dmg in dmg_lst if dmg]

    def apply_dmg(self, target, damage):
        """applies damage to target, called by attack() and
        apply_queued() returns damage applied"""
        damage = min(damage, target.hp)
        target.hp -= damage
        if target.hp <= 0:
            self.bury(target)
        return damage

    def bury(self, unit):
        """moves unit to graveyard"""
        x, y = unit.location
        unit.hp = 0
        unit.DOD = datetime.utcnow()
        self.grid[x][y].contents = None
        unit.location = Loc(-1, -1)
        del self.dmg_queue[unit]
        self.graveyard.append(unit)

    def attack(self, atkr, target):
        """calls calc_damage, applies result, Handles death."""
        defdr = self.grid[target[0]][target[1]].contents
        if defdr is None:
            raise ValueError('Nothing to attack at {0}'.format(target))
        defdr = getattr(defdr, 'nescient', defdr)
        dmg = self.calc_damage(atkr, defdr, target)
        defdr_HPs = []
        dot = (atkr.weapon.type in self.DOT)
        for unit, amt in dmg:
            if unit.hp > 0:
                if dot:
                    self.dmg_queue[defdr].append([amt, (atkr.weapon.time - 1)])
                defdr_HPs.append([unit, self.apply_dmg(unit, amt)])
        return defdr_HPs

    def get_dmg_queue(self):
        """returns a copy of the dmg_queue."""
        return {unit: dmgs[:] for unit, dmgs in self.dmg_queue.iteritems()}

    def apply_queued(self):
        """applies damage to targets stored in dmg_queue"""
        defdr_HPs = []
        for unit, dmgs in self.dmg_queue.iteritems():
            total = 0
            for n, dmg_tick in enumerate(dmgs):
                total += dmg_tick[0]
                dmg_tick[1] -= 1
            # Apply all damage we encountered this turn
            if total:
                defdr_HPs.append([unit, self.apply_dmg(unit, total)])
            # Filter out decayed DOT damage
            self.dmg_queue[unit] = [x for x in dmgs if x[1] > 0]
        return defdr_HPs
