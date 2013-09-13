from flask.ext.login import login_required, current_user
from equanimity.stronghold import Stronghold
from server import rpc


def _get_thing(cls, uid, name=None):
    if name is None:
        name = cls.__name__
    thing = cls.get(uid)
    if thing is None:
        raise ValueError('Invalid {name} {uid}'.format(name=name, uid=uid))
    if thing.owner != current_user:
        raise ValueError('You do not own this {name}'.format(name=name))


def _get_stronghold(field_location, **kwargs):
    return _get_thing(Stronghold, field_location, **kwargs)


@login_required
@rpc.method('equanimity.place_unit(list, int, list) -> dict', validate=True)
def place_unit(field_location, unit_id, grid_location):
    # TODO -- implement on stronghold
    # needs to move the unit from the stronghold to a battlefield
    pass


@login_required
@rpc.method('equanimity.name_unit(list, int, str) -> dict', validate=True)
def name_unit(field_location, unit_id, name):
    stronghold = _get_stronghold(field_location)
    unit = stronghold.name_unit(unit_id, name)
    return unit.api_view()


@login_required
@rpc.method('equanimity.equip_scient(list, int, int) -> dict', validate=True)
def equip_scient(field_location, unit_id, weapon_num):
    stronghold = _get_stronghold(field_location)
    unit = stronghold.equip_scient(unit_id, weapon_num)
    return unit.api_view()


@login_required
@rpc.method('equanimity.unequip_scient(list, int) -> dict', validate=True)
def unequip_scient(field_location, unit_id):
    stronghold = _get_stronghold(field_location)
    weapon = stronghold.unequip_scient(unit_id)
    return weapon.api_view()


@login_required
@rpc.method('equanimity.imbue_unit(list, dict, int) -> dict', validate=True)
def imbue_unit(field_location, comp, unit_id):
    stronghold = _get_stronghold(field_location)
    unit = stronghold.imbue_unit(comp, unit_id)
    return unit.api_view()


@login_required
@rpc.method('equanimity.form_weapon(list, str, dict, str) -> dict',
            validate=True)
def form_weapon(field_location, element, comp, weapon_type):
    stronghold = _get_stronghold(field_location)
    weapon = stronghold.form_weapon(element, comp, weapon_type)
    return weapon.api_view()


@login_required
@rpc.method('equanimity.split_weapon(list, dict, int) -> dict', validate=True)
def split_weapon(field_location, comp, weapon_num):
    stronghold = _get_stronghold(field_location)
    weapon = stronghold.split_weapon(comp, weapon_num)
    return weapon.api_view()


@login_required
@rpc.method('equanimity.imbue_weapon(list, dict, int) -> dict', validate=True)
def imbue_weapon(field_location, comp, weapon_num):
    stronghold = _get_stronghold(field_location)
    weapon = stronghold.imbue_weapon(comp, weapon_num)
    return weapon.api_view()


@login_required
@rpc.method('equanimity.form_squad(list, list, name=str) -> dict',
            validate=True)
def form_squad(field_location, unit_ids, name=None):
    stronghold = _get_stronghold(field_location)
    squad = stronghold.form_squad(unit_ids, name=name)
    return squad.api_view()


@login_required
@rpc.method('equanimity.name_squad(list, int, str) -> dict', validate=True)
def name_squad(field_location, squad_num, name):
    stronghold = _get_stronghold(field_location)
    squad = stronghold.name_squad(squad_num, name)
    return squad.api_view()


@login_required
@rpc.method('equanimity.remove_squad(list, int)', validate=True)
def remove_squad(field_location, squad_num):
    stronghold = _get_stronghold(field_location)
    squads = stronghold.remove_squad(squad_num)
    return [s.api_view() for s in squads]
