"""
battlefield.py

Created by AFD on 2013-08-05.
Copyright (c) 2013 A. Frederick Dudley. All rights reserved.
"""
"""contains battlefield objects"""
from datetime import datetime
from bidict import inverted
from stone import Stone, Composition
from units import Scient, Nescient, Part
from grid import Hex, HexCube

"""
Refactoring notes:
Grid should not be modified directly, should be a call to a Grid method
Replace ValueError with a custom exception
"""


class Battlefield(object):
    """contains grid, units and the logic for unit damage and movement."""
    def __init__(self, field, defsquad, atksquad):
        self.game_id = 0
        self.grid = field.grid
        self.field = field
        self.element = field.element
        self.graveyard = []
        self.defsquad = defsquad
        self.atksquad = atksquad
        self.dmg_queue = {}
        self.squads = (self.defsquad, self.atksquad)
        self.units = self.get_units()
        self.ranged = ('Bow', 'Magma', 'Firestorm', 'Forestfire',
                       'Pyrocumulus')
        self.DOT = ('Glove', 'Firestorm', 'Icestorm', 'Blizzard',
                    'Pyrocumulus')
        self.AOE = ('Wand', 'Avalanche', 'Icestorm', 'Blizzard', 'Permafrost')
        self.Full = ('Sword', 'Magma', 'Avalanche', 'Forestfire', 'Permafrost')

    def get_units(self):
        """looks in squads, returns all units in squads."""
        # Squads should be made immutable somewhere in Battlefield.
        units = []
        for squad in self.squads:
            if squad is not None:
                for unit in squad:
                    units.append(unit)
        return tuple(units)

    @property
    def living_units(self):
        return tuple(u for u in self.units if u.hp > 0)

    def make_parts(self, part_locs):
        new_body = {}
        for name, part in part_locs.iteritems():
            new_body[name] = Part(None, part)
        return new_body

    def make_body(self, right, direction):
        # TODO -- steve (move this to grid)
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
        """checks if a body is grid.in_bounds"""
        for part in body.itervalues():
            if self.grid.in_bounds(part.location):
                return True
        return False

    def body_within_grid(self, body):
        for part in body.itervalues():
            if not self.grid.in_bounds(part.location):
                return False
        return True

    def can_move_nescient(self, body, nescient):
        """checks if nescient can move to body."""
        if not self.body_within_grid(body):
            return False
        for part in body.itervalues():
            tile = self.grid.get(part.location)
            empty = (tile.contents is None)
            in_self = (tile.contents in nescient.body.itervalues())
            ctype = getattr(tile.contents, '__class__', None)
            is_stone = (ctype == Stone)
            if not empty and not in_self and not is_stone:
                return False
        return True

    def move_nescient(self, new_body, nescient, direction=None):
        """places new_body on grid, place body in nescient."""
        if not self.can_move_nescient(new_body, nescient):
            msg = 'Nescient cannot be moved to {0}'
            raise ValueError(msg.format(new_body))
        for part in new_body.itervalues():
            self.grid.get(part.location).contents = part
        nescient.take_body(new_body)
        nescient.location = nescient.body['right'].location
        if direction is not None:
            nescient.facing = direction
        return True

    def place_nescient(self, nescient, dest=None):
        """place a nescient so that its right is at dest."""
        if not nescient.location.is_null():
            raise ValueError('Nescient has already been placed')
        if dest is None:
            dest = nescient.chosen_location
        if dest.is_null():
            msg = 'Nescient {0} does not have a place to be'
            raise ValueError(msg.format(nescient))
        facing = nescient.facing
        if facing is None:
            facing = 'North'
        xdest, ydest = dest
        if not self.grid.in_bounds(dest):
            raise ValueError('Destination {0} is not on grid'.format(dest))
        new_body = self.make_body(dest, facing)
        self.dmg_queue.setdefault(nescient, [])
        return self.move_nescient(new_body, nescient, direction=facing)

    def get_rotations(self, nescient):
        """returns list of directions nescient can rotate."""
        drctns = []
        nbdr = nescient.body['right'].location
        for direction, _ in inverted(self.grid.directions):
            body = self.make_body(nbdr, direction)
            if self.can_move_nescient(body, nescient):
                drctns.append(direction)  # might want to return body as well.
        return drctns

    def put_squads_on_field(self):
        # TODO -- automatically assign field positions if unassigned
        for unit in self.defsquad:
            self.place_object(unit)
        for unit in self.atksquad:
            # Attackers are placed on the opposite side
            loc = unit.chosen_location
            loc = Hex(-loc[0], -loc[1])
            self.place_object(unit, dest=loc)

    def rotate(self, nescient, direction):
        """rotates Nescient so that head is facing direction"""
        new_body = self.make_body(nescient.body['right'].location, direction)
        return self.move_nescient(new_body, nescient, direction=direction)

    def map_to_grid(self, location, weapon):
        """returns tiles within range of location using weapon.
        called in hex_view.py"""
        xpos, ypos = location
        if weapon.type in self.ranged or weapon.type in self.AOE:
            move = 4
            no_hit = self.grid.tiles_in_range(location, move)
            hit = self.grid.tiles_in_range(location, 2 * move)
            return hit - no_hit
        else:
            return self.grid.get_adjacent(location)

    def place_object(self, obj, dest=None):
        """places an object on a tile."""
        if isinstance(obj, Scient):
            return self.place_scient(obj, dest=dest)
        elif isinstance(obj, Nescient):
            return self.place_nescient(obj, dest=dest)
        elif isinstance(obj, Stone):
            # TODO -- should the stone be placed or what?
            raise NotImplementedError('Placing stones is not ready')
        else:
            raise TypeError("{0} is not a game item.".format(obj))

    def move_scient(self, src, dest):
        """move unit from src tile to dest tile"""
        if src == dest:  # No action
            return False
        src = Hex._make(src)
        dest = Hex._make(dest)
        src_tile = self.grid.get(src)
        if src.distance(dest) > src_tile.contents.move:
            msg = "Tried moving more than {0} tiles"
            raise ValueError(msg.format(src_tile.contents.move))
        dest_tile = self.grid.get(dest)
        src_tile.move_contents_to(dest_tile)
        return True

    def place_scient(self, scient, dest=None):
        if not scient.location.is_null():
            raise ValueError('Scient was already placed on battlefield')
        if dest is None:
            dest = scient.chosen_location
        if dest.is_null():
            msg = 'Scient {0} does not have a place to be'
            raise ValueError(msg.format(scient))
        if not self.grid.in_bounds(dest):
            raise ValueError('Destination {0} is not on grid'.format(dest))
        scient.location = dest
        self.dmg_queue.setdefault(scient, [])
        self.grid.get(dest).set_contents(scient)
        return True

    def flush_units(self):
        """
        remove all units from grid, returns number of units flushed,
        does not put them in the graveyard. (for testing)
        """
        return len([t for t in self.grid.iter_tiles() if t.flush()])

    """ Attack / Damage methods """

    def dmg(self, atkr, defdr):
        """Calculates the damage of an attack"""
        dloc = defdr.location
        damage_dealt = Composition(0)
        if not self.grid.in_bounds(dloc):
            raise ValueError("Defender is off grid")

        if atkr.weapon.kind == 'p':
            for element in damage_dealt:
                dmg = ((atkr.p + atkr.patk + (2 * atkr.comp[element]) +
                        atkr.weapon.comp[element]) -
                       (defdr.p + defdr.pdef + (2 * defdr.comp[element]) +
                        self.grid.get(dloc).comp[element]))
                dmg = max(dmg, 0)
                damage_dealt[element] = dmg
            damage = sum(damage_dealt.values())
            return damage
        else:
            for element in damage_dealt:
                dmg = ((atkr.m + atkr.matk + (2 * atkr.comp[element]) +
                        atkr.weapon.comp[element]) -
                       (defdr.m + defdr.mdef + (2 * defdr.comp[element]) +
                        self.grid.get(dloc).comp[element]))
                dmg = max(dmg, 0)
                damage_dealt[element] = dmg

            damage = sum(damage_dealt.values())
            if atkr.element == defdr.element:
                return -damage
            else:
                return damage

    def calc_aoe(self, atkr, target):
        """Returns the AOE of a spell.
        The AOE is the cross-sectional line of the sextant that contains
        the target, relative to the attacker location
        """
        target = Hex._make(target)
        # Find the direction we should be facing
        direction = self.grid.get_direction(atkr.location, target)
        # Get primary and nonprimary coordinate
        primary = HexCube.primaries[direction]
        nonprimary = HexCube.nonprimaries[direction]
        # Convert to cube coords, relative to origin
        t = HexCube.from_hex(target - atkr.location)
        # Determine ranges that the nonprimary coordinates follow
        pval = getattr(t, primary)
        if pval < 0:
            r = range(0, -pval + 1)
        else:
            r = range(0, -pval - 1, -1)
        # Create the coordinates along the AOE cross-sectional line
        hex_cubes = []
        for a, b in zip(r, reversed(r)):
            coords = {}
            coords[primary] = pval
            coords[nonprimary[0]] = a
            coords[nonprimary[1]] = b
            hex_cubes.append(HexCube(**coords))
        # Convert back to axial coordinates and adjust back to atkr's loc
        tiles = [Hex.from_cube(h) + atkr.location for h in hex_cubes]
        return set(self.grid.filter_tiles(tiles))

    def calc_ranged(self, atkr, target):
        """UGH"""
        # use something like get_rotations to target 4 tiles at a time.
        # maybe it should magically hit 4 contigious tiles?
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
            msg = ("Defenders' locations: {0} is outside of attacker's " +
                   "range, located at {1}")
            raise ValueError(msg.format(dlocs, aloc))

        if target_loc is None:
            target_loc = defdr.location

        # calculate how many units will be damaged.
        if weapon.type in self.AOE:
            pat = self.calc_aoe(atkr, target_loc)
            targets = list(set(self.grid.occupied_coords()) & set(pat))
            area = len(pat)
            for t in targets:
                defdr = self.grid.get(t).contents
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
        unit.hp = 0
        unit.DOD = datetime.utcnow()
        self.grid.get(unit.location).contents = None
        unit.location = Hex.null
        del self.dmg_queue[unit]
        self.graveyard.append(unit)

    def attack(self, atkr, target):
        """calls calc_damage, applies result, Handles death."""
        defdr = self.grid.get(target).contents
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
