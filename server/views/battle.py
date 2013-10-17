from flask import Blueprint
from equanimity.battle import Action
from server import rpc
from server.decorators import require_login
from server.views.common import get_unit, get_field as _get_field


battle = Blueprint('battle', __name__, url_prefix='/api/battle')


def get_field(loc, **kwargs):
    field = _get_field(loc, **kwargs)
    if not field.in_battle:
        raise ValueError('No game is active for this field')
    return field


@rpc.method('battle.pass(list, int) -> dict')
@require_login
def pass_turn(field_loc, unit_id):
    # Field coord, Unit, type, target
    field = get_field(field_loc)
    unit = get_unit(unit_id)
    action = Action(unit=unit, type='pass')
    return field.game.process_action(action)


@rpc.method('battle.move(list, int, list) -> dict')
@require_login
def move(field_loc, unit_id, target):
    field = get_field(field_loc)
    unit = get_unit(unit_id)
    action = Action(unit=unit, type='move', target=target)
    return field.game.process_action(action)


@rpc.method('battle.attack(list, int, list) -> dict')
@require_login
def attack(field_loc, unit_id, target):
    field = get_field(field_loc)
    unit = get_unit(unit_id)
    action = Action(unit=unit, type='attack', target=target)
    return field.game.process_action(action)
