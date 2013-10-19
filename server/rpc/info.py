from flask import Blueprint
from flask.ext.login import current_user
from server import jsonrpc
from server.decorators import require_login
from server.rpc.common import get_field, get_unit, get_battle


info = Blueprint('info', __name__, url_prefix='/api/info')


@jsonrpc.method('info.world() -> dict')
@require_login
def world_info():
    return dict(world=current_user.world_view())


@jsonrpc.method('info.field(list) -> dict')
@require_login
def field_info(field_loc):
    field = get_field(field_loc)
    data = field.api_view(requester=current_user)
    return dict(field=data)


@jsonrpc.method('info.clock() -> dict')
@require_login
def clock_info():
    # TODO -- once clock is implemented fully, add this
    return dict(clock=dict())


@jsonrpc.method('info.battle(list) -> dict')
@require_login
def battle_info(field_loc):
    battle = get_battle(field_loc)
    return dict(battle=battle.api_view())


@jsonrpc.method('info.battle_timer(list) -> dict')
@require_login
def battle_timer_info(field_loc):
    battle = get_battle(field_loc)
    return dict(battle=dict(timer=battle.timer_view()))


@jsonrpc.method('info.unit(int) -> dict')
@require_login
def unit_info(unit_id):
    unit = get_unit(unit_id, check_owner=False)
    # TODO -- apply any restrictions to viewing others' units
    # Some info will need to be exposed in battle, at the very least
    return dict(unit=unit.api_view())
