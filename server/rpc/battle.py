from flask import Blueprint
from equanimity.battle import Action
from server import jsonrpc
from server.decorators import require_login, commit
from server.rpc.common import get_unit, get_field as _get_field


battle = Blueprint('battle', __name__, url_prefix='/api/battle')


def get_field(world_id, loc, **kwargs):
    field = _get_field(world_id, loc, **kwargs)
    if not field.in_battle:
        raise ValueError('No game is active for this field')
    return field


@jsonrpc.method('battle.pass(int, list, int) -> dict', validate=True)
@require_login
@commit
def pass_turn(world_id, field_loc, unit_id):
    # Field coord, Unit, type, target
    field = get_field(world_id, field_loc)
    unit = get_unit(unit_id)
    action = Action(unit=unit, type='pass')
    return field.battle.process_action(action).api_view()


@jsonrpc.method('battle.move(int, list, int, list) -> dict', validate=True)
@require_login
@commit
def move(world_id, field_loc, unit_id, target):
    field = get_field(world_id, field_loc)
    unit = get_unit(unit_id)
    action = Action(unit=unit, type='move', target=target)
    return field.battle.process_action(action).api_view()


@jsonrpc.method('battle.attack(int, list, int, list) -> dict', validate=True)
@require_login
@commit
def attack(world_id, field_loc, unit_id, target):
    field = get_field(world_id, field_loc)
    unit = get_unit(unit_id)
    action = Action(unit=unit, type='attack', target=target)
    return field.battle.process_action(action).api_view()
