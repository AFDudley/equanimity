from flask import Blueprint
from flask.ext.login import current_user
from server import jsonrpc
from server.decorators import require_login
from server.rpc.common import (get_field, get_unit, get_stronghold, get_world,
                               get_battle_by_id, get_battle)
                               
field = Blueprint('field', __name__, url_prefix='/api/field')


@jsonrpc.method('field.tick(int, list) -> int', validate=True)
@require_login
def field_tick(world_id, field_loc):
    f = get_field(world_id, field_loc)
    if not f.queue.queue:
        raise ValueError("Field queue is empty")
    f.clock.change_day(f)
    return
