from flask import Blueprint
from flask.ext.login import current_user
from server import jsonrpc
from server.decorators import require_login
from server.rpc.common import (get_field, get_unit, get_battle, get_stronghold,
                               get_world)


info = Blueprint('info', __name__, url_prefix='/api/info')


@jsonrpc.method('info.world(int) -> dict', validate=True)
@require_login
def world_info(world_id):
    return dict(world=current_user.world_view(world_id))


@jsonrpc.method('info.clock(int) -> dict', validate=True)
@require_login
def clock_info(world_id):
    return dict(clock=get_world(world_id).clock.api_view())


@jsonrpc.method('info.field(int, list) -> dict', validate=True)
@require_login
def field_info(world_id, field_loc):
    field = get_field(world_id, field_loc)
    data = field.api_view(requester=current_user)
    return dict(field=data)


@jsonrpc.method('info.battle(int, list) -> dict', validate=True)
@require_login
def battle_info(world_id, field_loc):
    battle = get_battle(world_id, field_loc)
    return dict(battle=battle.api_view())


@jsonrpc.method('info.battle_timer(int, list) -> dict', validate=True)
@require_login
def battle_timer_info(world_id, field_loc):
    battle = get_battle(world_id, field_loc)
    return dict(battle=dict(timer=battle.timer_view()))


@jsonrpc.method('info.unit(int) -> dict', validate=True)
@require_login
def unit_info(unit_id):
    unit = get_unit(unit_id, check_owner=False)
    # TODO -- apply any restrictions to viewing others' units
    # Some info will need to be exposed in battle, at the very least
    return dict(unit=unit.api_view())


@jsonrpc.method('info.stronghold(int, list) -> dict', validate=True)
@require_login
def stronghold_info(world_id, field_loc):
    stronghold = get_stronghold(world_id, field_loc)
    return dict(stronghold=stronghold.api_view())
