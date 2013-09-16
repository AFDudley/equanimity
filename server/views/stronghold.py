import transaction
from flask import Blueprint
from flask.ext.login import current_user
from equanimity.stronghold import Stronghold
from server import rpc
from server.decorators import require_login


stronghold = Blueprint('stronghold', __name__, url_prefix='/api')


def _get_thing(cls, uid, name=None):
    if name is None:
        name = cls.__name__
    thing = cls.get(uid)
    if thing is None:
        raise ValueError('Invalid {name} {uid}'.format(name=name, uid=uid))
    if thing.owner != current_user:
        raise ValueError('You do not own this {name}'.format(name=name))
    return thing


def _get_stronghold(field_location, **kwargs):
    return _get_thing(Stronghold, field_location, **kwargs)


@rpc.method('equanimity.place_unit(list, int, list) -> dict', validate=True)
@require_login
def place_unit(field_location, unit_id, grid_location):
    # TODO -- implement on stronghold
    # needs to move the unit from the stronghold to a battlefield
    pass


@rpc.method('equanimity.name_unit(list, int, str) -> dict', validate=True)
@require_login
def name_unit(field_location, unit_id, name):
    stronghold = _get_stronghold(field_location)
    unit = stronghold.name_unit(unit_id, name)
    transaction.commit()
    return dict(unit=unit.api_view())


@rpc.method('equanimity.equip_scient(list, int, int) -> dict', validate=True)
@require_login
def equip_scient(field_location, unit_id, weapon_num):
    stronghold = _get_stronghold(field_location)
    unit = stronghold.equip_scient(unit_id, weapon_num)
    return dict(unit=unit.api_view())


@rpc.method('equanimity.unequip_scient(list, int) -> dict', validate=True)
@require_login
def unequip_scient(field_location, unit_id):
    stronghold = _get_stronghold(field_location)
    weapon = stronghold.unequip_scient(unit_id)
    transaction.commit()
    return dict(weapon=weapon.api_view())


@rpc.method('equanimity.imbue_unit(list, dict, int) -> dict', validate=True)
@require_login
def imbue_unit(field_location, comp, unit_id):
    stronghold = _get_stronghold(field_location)
    unit = stronghold.imbue_unit(comp, unit_id)
    transaction.commit()
    return dict(unit=unit.api_view())


@rpc.method('equanimity.split_weapon(list, dict, int) -> dict', validate=True)
@require_login
def split_weapon(field_location, comp, weapon_num):
    stronghold = _get_stronghold(field_location)
    weapon = stronghold.split_weapon(comp, weapon_num)
    transaction.commit()
    return dict(weapon=weapon.api_view())


@rpc.method('equanimity.imbue_weapon(list, dict, int) -> dict', validate=True)
@require_login
def imbue_weapon(field_location, comp, weapon_num):
    stronghold = _get_stronghold(field_location)
    weapon = stronghold.imbue_weapon(comp, weapon_num)
    transaction.commit()
    return dict(weapon=weapon.api_view())


@rpc.method('equanimity.form_squad(list, list) -> dict', validate=True)
@require_login
def form_squad(field_location, unit_ids):
    stronghold = _get_stronghold(field_location)
    squad = stronghold.form_squad(unit_ids)
    transaction.commit()
    return dict(squad=squad.api_view())


@rpc.method('equanimity.name_squad(list, int, str) -> dict', validate=True)
@require_login
def name_squad(field_location, squad_num, name):
    stronghold = _get_stronghold(field_location)
    squad = stronghold.name_squad(squad_num, name)
    transaction.commit()
    return dict(squad=squad.api_view())


@rpc.method('equanimity.remove_squad(list, int)', validate=True)
@require_login
def remove_squad(field_location, squad_num):
    stronghold = _get_stronghold(field_location)
    stronghold.remove_squad(squad_num)
    transaction.commit()
    return dict(squads=[s.api_view() for s in stronghold.squads])
