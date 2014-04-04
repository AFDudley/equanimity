from flask import Blueprint
from flask.ext.login import current_user
from server import jsonrpc
from server.decorators import require_login
from server.rpc.common import (get_field, get_unit, get_stronghold, get_world,
                               get_battle_by_id, get_battle)


info = Blueprint('info', __name__, url_prefix='/api/info')


@jsonrpc.method('info.world_has_fields(int) -> bool', valdiate=True)
@require_login
def world_has_fields(world_id):
    return dict(has_fields=get_world(world_id).has_fields)


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


@jsonrpc.method('info.field_battle(int, list) -> dict', validate=True)
@require_login
def field_battle_info(world_id, field_loc):
    battle = get_battle(world_id, field_loc)
    return dict(battle=battle.api_view())


@jsonrpc.method('info.battle(int) -> dict', validate=True)
@require_login
def battle_info(battle_id):
    battle = get_battle_by_id(battle_id)
    return dict(battle=battle.api_view())


@jsonrpc.method('info.battle_timer(int) -> dict', validate=True)
@require_login
def battle_timer_info(battle_id):
    battle = get_battle_by_id(battle_id)
    return dict(battle=dict(uid=battle.uid, timer=battle.timer_view()))


@jsonrpc.method('info.battle_states(int) -> dict', validate=True)
@require_login
def battle_states_info(battle_id):
    battle = get_battle_by_id(battle_id)
    return dict(battle=dict(uid=battle.uid, states=battle.states_view()))


@jsonrpc.method('info.battle_messages(int) -> dict', validate=True)
@require_login
def battle_messages_info(battle_id):
    battle = get_battle_by_id(battle_id)
    return dict(battle=dict(uid=battle.uid, messages=battle.messages_view()))


@jsonrpc.method('info.battle_actions(int) -> dict', validate=True)
@require_login
def battle_actions_info(battle_id):
    battle = get_battle_by_id(battle_id)
    return dict(battle=dict(uid=battle.uid, actions=battle.actions_view()))


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
