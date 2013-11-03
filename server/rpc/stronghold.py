import transaction
from flask import Blueprint
from equanimity.unit_container import Squad
from server import jsonrpc
from server.decorators import require_login
from server.rpc.common import get_unit, get_stronghold


stronghold = Blueprint('stronghold', __name__, url_prefix='/api/stronghold')


@jsonrpc.method('stronghold.place_unit(int, list) -> dict', validate=True)
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


@jsonrpc.method('stronghold.name_unit(int, list, int, str) -> dict',
                validate=True)
@require_login
def name_unit(world_id, field_location, unit_id, name):
    stronghold = get_stronghold(world_id, field_location)
    unit = stronghold.name_unit(unit_id, name)
    transaction.commit()
    return dict(unit=unit.api_view())


@jsonrpc.method('stronghold.equip_scient(int, list, int, int) -> dict',
                validate=True)
@require_login
def equip_scient(world_id, field_location, unit_id, weapon_num):
    stronghold = get_stronghold(world_id, field_location)
    unit = stronghold.equip_scient(unit_id, weapon_num)
    transaction.commit()
    return dict(unit=unit.api_view())


@jsonrpc.method('stronghold.unequip_scient(int, list, int) -> dict',
                validate=True)
@require_login
def unequip_scient(world_id, field_location, unit_id):
    stronghold = get_stronghold(world_id, field_location)
    weapon = stronghold.unequip_scient(unit_id)
    transaction.commit()
    return dict(weapon=weapon.api_view())


@jsonrpc.method('stronghold.imbue_unit(int, list, dict, int) -> dict',
                validate=True)
@require_login
def imbue_unit(world_id, field_location, comp, unit_id):
    stronghold = get_stronghold(world_id, field_location)
    unit = stronghold.imbue_unit(comp, unit_id)
    transaction.commit()
    return dict(unit=unit.api_view())


@jsonrpc.method('stronghold.split_weapon(int, list, dict, int) -> dict',
                validate=True)
@require_login
def split_weapon(world_id, field_location, comp, weapon_num):
    stronghold = get_stronghold(world_id, field_location)
    weapon = stronghold.split_weapon(comp, weapon_num)
    transaction.commit()
    return dict(weapon=weapon.api_view())


@jsonrpc.method('stronghold.imbue_weapon(int, list, dict, int) -> dict',
                validate=True)
@require_login
def imbue_weapon(world_id, field_location, comp, weapon_num):
    stronghold = get_stronghold(world_id, field_location)
    weapon = stronghold.imbue_weapon(comp, weapon_num)
    transaction.commit()
    return dict(weapon=weapon.api_view())


@jsonrpc.method('stronghold.form_squad(int, list, list) -> dict',
                validate=True)
@require_login
def form_squad(world_id, field_location, unit_ids):
    stronghold = get_stronghold(world_id, field_location)
    squad = stronghold.form_squad(unit_ids)
    transaction.commit()
    return dict(squad=squad.api_view())


@jsonrpc.method('stronghold.name_squad(int, list, int, str) -> dict',
                validate=True)
@require_login
def name_squad(world_id, field_location, squad_num, name):
    stronghold = get_stronghold(world_id, field_location)
    squad = stronghold.name_squad(squad_num, name)
    transaction.commit()
    return dict(squad=squad.api_view())


@jsonrpc.method('stronghold.remove_squad(int, list, int)', validate=True)
@require_login
def remove_squad(world_id, field_location, squad_num):
    stronghold = get_stronghold(world_id, field_location)
    stronghold.remove_squad(squad_num)
    transaction.commit()
    return dict(squads=[s.api_view() for s in stronghold.squads])
