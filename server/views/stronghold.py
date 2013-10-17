import transaction
from flask import Blueprint
from equanimity.unit_container import Squad
from server import rpc
from server.decorators import require_login
from server.views.common import get_unit, get_stronghold


stronghold = Blueprint('stronghold', __name__, url_prefix='/api/stronghold')


@rpc.method('stronghold.place_unit(int, list) -> dict', validate=True)
@require_login
def place_unit(unit_id, grid_location):
    unit = get_unit(unit_id)
    squad = unit.container
    if not isinstance(squad, Squad):
        raise ValueError('Unit isn\'t in a squad')
    stronghold = squad.stronghold
    if stronghold is None:
        raise ValueError('Unit\'s squad isn\'t in a stronghold')
    stronghold.field.place_scient(unit, grid_location)
    transaction.commit()
    return dict(unit=unit.api_view())


@rpc.method('stronghold.name_unit(list, int, str) -> dict', validate=True)
@require_login
def name_unit(field_location, unit_id, name):
    stronghold = get_stronghold(field_location)
    unit = stronghold.name_unit(unit_id, name)
    transaction.commit()
    return dict(unit=unit.api_view())


@rpc.method('stronghold.equip_scient(list, int, int) -> dict', validate=True)
@require_login
def equip_scient(field_location, unit_id, weapon_num):
    stronghold = get_stronghold(field_location)
    unit = stronghold.equip_scient(unit_id, weapon_num)
    transaction.commit()
    return dict(unit=unit.api_view())


@rpc.method('stronghold.unequip_scient(list, int) -> dict', validate=True)
@require_login
def unequip_scient(field_location, unit_id):
    stronghold = get_stronghold(field_location)
    weapon = stronghold.unequip_scient(unit_id)
    transaction.commit()
    return dict(weapon=weapon.api_view())


@rpc.method('stronghold.imbue_unit(list, dict, int) -> dict', validate=True)
@require_login
def imbue_unit(field_location, comp, unit_id):
    stronghold = get_stronghold(field_location)
    unit = stronghold.imbue_unit(comp, unit_id)
    transaction.commit()
    return dict(unit=unit.api_view())


@rpc.method('stronghold.split_weapon(list, dict, int) -> dict', validate=True)
@require_login
def split_weapon(field_location, comp, weapon_num):
    stronghold = get_stronghold(field_location)
    weapon = stronghold.split_weapon(comp, weapon_num)
    transaction.commit()
    return dict(weapon=weapon.api_view())


@rpc.method('stronghold.imbue_weapon(list, dict, int) -> dict', validate=True)
@require_login
def imbue_weapon(field_location, comp, weapon_num):
    stronghold = get_stronghold(field_location)
    weapon = stronghold.imbue_weapon(comp, weapon_num)
    transaction.commit()
    return dict(weapon=weapon.api_view())


@rpc.method('stronghold.form_squad(list, list) -> dict', validate=True)
@require_login
def form_squad(field_location, unit_ids):
    stronghold = get_stronghold(field_location)
    squad = stronghold.form_squad(unit_ids)
    transaction.commit()
    return dict(squad=squad.api_view())


@rpc.method('stronghold.name_squad(list, int, str) -> dict', validate=True)
@require_login
def name_squad(field_location, squad_num, name):
    stronghold = get_stronghold(field_location)
    squad = stronghold.name_squad(squad_num, name)
    transaction.commit()
    return dict(squad=squad.api_view())


@rpc.method('stronghold.remove_squad(list, int)', validate=True)
@require_login
def remove_squad(field_location, squad_num):
    stronghold = get_stronghold(field_location)
    stronghold.remove_squad(squad_num)
    transaction.commit()
    return dict(squads=[s.api_view() for s in stronghold.squads])
