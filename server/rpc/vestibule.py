from flask import Blueprint
from flask.ext.login import current_user
from equanimity.vestibule import Vestibule
from server import jsonrpc
from server.decorators import require_login, commit
from server.rpc.common import get_thing
from server import db
from worker.tasks import start_vestibule_task
from worker.world_tasks import start_task
vestibule = Blueprint('vestibule', __name__, url_prefix='/api/vestibule')


def _get_vestibule(uid, is_member=None, no_world=True):
    """Returns  vestibule by uid.  If check_membership_status is given, it
    should be a bool and its value will be compared to the result of
    vestibule.players.has(). I.e. if you want to confirm the player is not
    in the vestibule already, use is_member=False
    If no_world is True, then an error will be raised if this Vestibule
    already has a World associated with it
    """
    v = get_thing(Vestibule, (uid,), check_owner=False)
    if is_member is not None:
        has = v.players.has(current_user._get_current_object())
        if has and not is_member:
            raise ValueError('Player is in vestibule')
        elif not has and is_member:
            raise ValueError('Player is not in vestibule')
    if no_world and v.world is not None:
        raise ValueError('Vestibule already has a World')
    return v


@jsonrpc.method('vestibule.create() -> dict', validate=True)
@require_login
@commit
def create_vestibule():
    v = Vestibule()
    p = current_user._get_current_object()
    v.players.add(p)
    v.players.set_leader(p)
    v.persist()
    return dict(vestibule=v.api_view())


@jsonrpc.method('vestibule.join(int) -> dict', validate=True)
@require_login
@commit
def join_vestibule(vestibule_id):
    v = _get_vestibule(vestibule_id, is_member=False)
    v.players.add(current_user._get_current_object())
    return dict(vestibule=v.api_view())


@jsonrpc.method('vestibule.leave(int) -> dict', validate=True)
@require_login
@commit
def leave_vestibule(vestibule_id):
    v = _get_vestibule(vestibule_id, is_member=True)
    v.players.remove(current_user._get_current_object())
    return dict(vestibule=v.api_view())


@jsonrpc.method('vestibule.start(int) -> dict', validate=True)
@require_login
@commit
def start_vestibule(vestibule_id):
    v = _get_vestibule(vestibule_id, is_member=True)
    # Only the leader can create the vestibule
    leader = v.players.get_leader(allow_world=False)
    p = current_user._get_current_object()
    if leader != p:
        raise ValueError('You cannot start this vestibule')
    w = v.start()
    start_task.delay(w.uid) # this shouldn't block
    return dict(world=dict(uid=w.uid))
    
@jsonrpc.method('vestibule.get(int) -> dict', validate=True)
@require_login
def get_vestibule(vestibule_id):
    v = _get_vestibule(vestibule_id, no_world=False)
    return dict(vestibule=v.api_view())


@jsonrpc.method('vestibule.list() -> dict', validate=True)
@require_login
def list_vestibules():
    vestibules = db['vestibules'].itervalues()
    return dict(vestibules=[v.api_view() for v in vestibules])
