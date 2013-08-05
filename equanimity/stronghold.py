"""
stronghold.py

Created by AFD on 2013-08-05.
Copyright (c) 2013 A. Frederick Dudley. All rights reserved.
"""
import persistent
import transaction

from stone import Stone
from units import Scient
from unit_container import Container, Squad
from weapons import Sword, Bow, Wand, Glove
from const import ELEMENTS, E, F, I, W, ORTH, OPP, WEP_LIST

from helpers import rand_string
from factory import Stable, Armory, Home, Farm
from silo import Silo
from copy import deepcopy
from clock import now

class mappedContainer(persistent.Persistent, Container):
    def __init__(self):
        Container.__init__(self, data=None, free_spaces=8)
        #maybe map should actually return the key and method
        #should be added instead of using .map
        self.map = persistent.mapping.PersistentMapping()
        self.name = 'stronghold'
    
    def __setitem__(self, key, val):
        Container.__setitem__(self, key, val)
        self.map.update({key.id: key})
    
    def __delitem__(self, key):
        del self.map[self.data[key].id]
        if self.data[key].container.name == 'stronghold':
            self.data[key].container = None
        temp = self[key].value()
        self.free_spaces += self.unit_size(self[key])
        self.data.__delitem__(key)
        self.val -= temp
    
    def append(self, item):
        Container.append(self, item)
        self.map.update({item.id: item})
    
    #FIX
    def remove_by_id(self, unit_id):
        k = None
        for u_key in reversed(xrange(len(self))):
            if self[u_key].id == unit_id:
                k = u_key
        del self[k]
    

class Stronghold(persistent.Persistent):
    def create_factory(self, kind):
        """Adds a factory to a stronghold, raises exception if factory already exists."""
        #factories should cost something.
        if kind =='Stable' or kind =='Earth':
            if not self.stable:
                self.stable = Stable()
            else:
                raise Exception("This stronghold already has a stable.")
        elif kind == 'Armory' or kind == 'Fire':
            if not self.armory:
                self.armory = Armory()
            else:
                raise Exception("This stronghold already has an armory.")
        elif kind == 'Home' or kind == 'Ice':
            if not self.home:
                self.home = Home()
            else:
                raise Exception("This stronghold already has a home.")
        elif kind == 'Farm' or kind == 'Wind':
            if not self.farm:
                self.farm = Farm()
            else:
                raise Exception("This stronghold already has a farm.")
        self._p_changed = 1
        return transaction.commit()
    
    def __init__(self, field_element, clock):
        self.clock = clock
        self.silo = Silo()
        self.weapons = persistent.list.PersistentList()
        self.units = mappedContainer()
        self.squads = persistent.list.PersistentList()
        self.defenders = Squad(name='Defenders')
        self.make_defenders(field_element)
        self.defender_locs = persistent.list.PersistentList()
        self.stable = None
        self.armory = None
        self.home = None
        self.farm = None
        self.create_factory(field_element)
        return transaction.commit()
    
    def form_weapon(self, element, comp, weap_type):
        """Takes a stone from stronghold and turns it into a Weapon."""
        #for testing!!!!!
        #!!!!!!!!WEAP_TYPE NEEDS TO BE CHECKED BEFORE PASSED TO EVAL!!!!!!!!!!!
        #(or I could just fix Weapon, duh)
        weapon = eval(weap_type)(element, self.silo.get(comp))
        self.weapons.append(weapon)
        self._p_changed = 1
        return transaction.commit()
    
    def imbue_weapon(self, comp, weapon_num):
        """Imbue a weapon with stone of comp from silo."""
        stone = self.silo.get(comp)
        self.silo._p_changed = 1
        self.weapons[weapon_num].imbue(stone)
        self.weapons[weapon_num]._p_changed = 1
        return transaction.commit()
    
    def split_weapon(self, comp, weapon_num):
        """Splits comp from weapon, places it in silo."""
        stone = self.weapons[weapon_num].split(comp)
        self.silo.imbue(stone)
        self.weapons[weapon_num]._p_changed = 1
        self.silo._p_changed = 1
        return transaction.commit()
    
    def form_scient(self, element, comp, name=None):
        """Takes a stone from stronghold and turns it into a Scient."""
        if name == None: name = rand_string()
        scient = Scient(element, self.silo.get(comp), name)
        self.units.append(scient)
        self.feed_unit(scient.id)
        self._p_changed = 1
        return transaction.commit()
    
    def name_unit(self, unit_id, name):
        unit = self.units.map[unit_id]
        unit.name = str(name)
        unit._p_changed = 1
        return transaction.commit()
    
    def imbue_unit(self, comp, unit_id):
        """Imbue a unit with stone of comp from silo."""
        stone = self.silo.get(comp)
        self.silo._p_changed = 1
        unit = self.units.map[unit_id]
        unit.imbue(stone)
        unit._p_changed = 1
        if unit.container.name != 'stronghold':
            unit.container.update_value()
            unit.container._p_changed = 1
        return transaction.commit()
    
    def unequip_scient(self, unit_id):
        """Moves a weapon from a scient to the stronghold."""
        scient = self.units.map[unit_id]
        self.weapons.append(scient.unequip())
        self.weapons._p_changed = 1
        scient._p_changed = 1
        self._p_changed = 1
        return transaction.commit()
    
    def equip_scient(self, unit_id, weapon_num):
        """Moves a weapon from the weapon list to a scient."""
        scient = self.units.map[unit_id]
        if scient.weapon:
            self.unequip_scient(unit_id)
        weapon = self.weapons[weapon_num]
        del self.weapons[weapon_num]
        scient.equip(weapon)
        self.weapons_p_changed =1
        scient._p_changed = 1
        self._p_changed = 1
        return transaction.commit()
    
    def form_squad(self, unit_id_list=None, name=None):
        """Forms a squad and places it in the stronghold."""
        if name == None: name = rand_string()
        sq = Squad(name=name)
        try:
            for unit_id in unit_id_list:
                unit = self.units.map[unit_id]
                if unit.container.name == 'stronghold':
                    sq.append(unit) #DOES NOT REMOVE UNIT FROM LIST.
                else:
                    raise Exception("%s is already in a container." %unit)
            self.squads.append(sq)
            self._p_changed = 1
            return transaction.commit()
        except:
            raise
    
    def name_squad(self, squad_num, name):
        squad = self.sqauds[squad_num]
        squad.name = str(name)
        squad._p_changed = 1
        return transaction.commit()
    
    def remove_squad(self, squad_num):
        """Removes units from from self.units, effectively moving the squad out
         of the stronghold."""
        squad = self.squads[squad_num]
        for unit in squad:
            self.units.remove_by_id(unit.id)
        return transaction.commit()
    
    def apply_locs_to_squad(self, squad, list_of_locs):
        """takes a list of locations and appliees them to the units in a squad"""
        #TODO loc sanity check. on_grid is a start, but not completely correct.
        if len(squad) == len(list_of_locs):
            for n in xrange(len(squad)):
                squad[n].location = list_of_locs[n]
                squad[n]._p_changed = 1
            return transaction.commit()
        else:
            raise Exception("The squad and the list of locations must be the same length.")
    
    def apply_squad_locs(self, squad_num, list_of_locs):
        return self.apply_locs_to_squad(self.squads[squad_num], list_of_locs)
    
    def set_defender_locs(self, list_of_locs):
        self.defender_locs = list_of_locs
        self._p_changed = 1
        return transaction.commit()
    
    def apply_defender_locs(self):
        return self.apply_locs_to_squad(self.defenders, self.defender_locs)
    
    def unset_defenders(self):
        """Moves old defenders into stronghold"""
        #use wisely.
        self.squads.append(self.defenders)
        self.defenders = None;
        self._p_changed = 1
        return transaction.commit()
    
    def set_defenders(self, squad_num):
        """If defenders is empty set squad as defenders."""
        # I don't remember how transactions work so I broke this function in
        # two, which might actually make it worse...
        
        # TODO: there should be a check to make sure the squad is not
        # stronger than the grid.
        # (Which is why self.defenders != self.squad[0])
        
        self.defenders = self.squads[squad_num]
        del self.squads[squad_num]
        self._p_changed = 1
        return transaction.commit()
    
    def make_defenders(self, element):
        """FIX"""
        s = Stone()
        s[element] = 4
        s[OPP[element]] = 0
        for o in ORTH[element]:
            s[o] = 2
        for n in xrange(8): self.silo.imbue(deepcopy(s))
        wcomp = Stone().comp
        for n in xrange(len(WEP_LIST)):
            wep = WEP_LIST[n]
            self.form_scient(element, s.comp)
            #you wanna race?
            unit_id = self.units[-1].id
            self.form_weapon(element, wcomp, wep)
            self.name_unit(unit_id , "Ms. " + wep)
            self.equip_scient(unit_id, -1)
            self.add_unit_to_defenders(unit_id)
    
    def move_squad_to_defenders(self, squad_num):
        """Moves a squad from self.squads to self.defenders"""
        try:
            self.unset_defenders()
            self.set_defenders(squad_num)
            return
        except:
            raise("There was an error moving squad to defenders.")
    
    def add_unit_to(self, container, unit_id):
        """Add unit to container."""
        #wrapper to keep containers private.
        container.append(self.units.map[unit_id])
        container._p_changed = 1
        return transaction.commit()
    
    def add_unit_to_defenders(self, unit_id):
        return self.add_unit_to(self.defenders, unit_id)
    
    def add_unit_to_factory(self, kind, unit_id):
        if kind == 'Stable':
            return self.add_unit_to(self.stable, unit_id)
        elif kind == 'Armory':
            return self.add_unit_to(self.armory, unit_id)
        elif kind == 'Home':
            return self.add_unit_to(self.home, unit_id)
        elif kind == 'Farm':
            return self.add_unit_to(self.farm, unit_id)
    
    def add_unit_to_squad(self, squad_num, unit_id):
        return self.add_unit_to(self, self.squads[squad_num], unit_id)
    
    def remove_unit_from(self, container, unit_id):
        """remove unit from container."""
        for n in xrange(len(container)):
            if container[n].id == unit_id:
                container[n].container = None
                del container[n]
        container._p_changed = 1
        return transaction.commit()
    
    def remove_unit_from_defenders(self, unit_id):
        return self.remove_unit_from(self.defenders, unit_id)
    
    def remove_unit_from_factory(self, kind, unit_id):
        if kind == 'Stable':
            return self.remove_unit_from(self.stable, unit_id)
        elif kind == 'Armory':
            return self.remove_unit_from(self.armory, unit_id)
        elif kind == 'Home':
            return self.remove_unit_from(self.home, unit_id)
        elif kind == 'Farm':
            return self.remove_unit_from(self.farm, unit_id)
    
    def remove_unit_from_squad(self, squad_num, unit_id):
        return self.remove_unit_from(self.squads[squad_num], unit_id)
    
    def bury_unit(self, unit_id):
        """Bury units that die outside of battle."""
        unit = self.units.map[unit_id]
        self.unequip_scient(unit)
        self.remove_unit_from(unit.container, unit.id)
        remains = Stone({k: v/2 for k,v in unit.iteritems()})
        self.silo.imbue(remains)
        return
    
    def feed_unit(self, unit_id): #maybe it should take a clock.
        """feeds a unit from the silo, most they can be fed is every 60 days"""
        # A scient eats their composition's worth of stones in 2 months. (60 days)
        # every two months from when the unit was born, discount the inventory the unit's value.
        # Two weeks without food a unit dies.
        
        def feed(unit, lnow):
            self.silo.get(unit.comp)
            self.silo._p_changed = 1
            unit.fed_on = now()
            unit._p_changed = 1
            return transaction.commit()
        
        unit = self.units.map[unit_id]
        lnow = now()
        if unit.fed_on == None:
            feed(unit, lnow)
        else:
            delta = lnow - unit.fed_on
            dsecs = delta.total_seconds()
            if dsecs > (self.clock.duration['day'] * 60):
                if dsecs < (self.clock.duration['day'] * 72):
                    feed(unit, lnow)
                else:
                    self.bury_unit(unit_id)
            else:
                pass #unit already fed.
    
    def feed_units(self):
        """Attempts to feed units. check happens every game day."""
        # 1. feed scients first.
        # 2. feed nescients.
        #should not happen when field is embattled.
        now = now()
        for unit in self.units:
            d = now - unit.fed_on
            dsecs = d.total_seconds()
            if dsecs > (self.clock.duration['day'] * 60):
                self.feed_unit(unit.id)
    

    def process_action(self, action):
        pass
