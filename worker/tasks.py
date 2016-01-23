from flask import Blueprint
from flask.ext.login import current_user
from equanimity.vestibule import Vestibule
from server import jsonrpc
from server.decorators import require_login, commit
from server.rpc.common import get_thing
from server import db, create_app
from celery import Celery
import config

celery = Celery(broker='redis://127.0.0.1:6379/0')
celery.conf.update(
    CELERY_BROKER_URL='redis://127.0.0.1:6379/0',
    CELERY_RESULT_BACKEND='redis://127.0.0.1:6379/0'
)

vestibule = Blueprint('vestibule', __name__, url_prefix='/api/vestibule')


def _get_vestibule(uid, is_member=None, no_world=True, player_id=None):
    """Returns  vestibule by uid.  If check_membership_status is given, it
    should be a bool and its value will be compared to the result of
    vestibule.players.has(). I.e. if you want to confirm the player is not
    in the vestibule already, use is_member=False
    If no_world is True, then an error will be raised if this Vestibule
    already has a World associated with it
    """
    v = get_thing(Vestibule, (uid,), check_owner=False)
    if is_member is not None:
        for p in v.players:
            if p.uid == player_id:
                has = True
        if has and not is_member:
            raise ValueError('Player is in vestibule')
        elif not has and is_member:
            raise ValueError('Player is not in vestibule')
    if no_world and v.world is not None:
        raise ValueError('Vestibule already has a World')
    return v



@celery.task()
@commit
def start_vestibule_task(vestibule_id, player_id):
    with create_app(config='production').test_request_context():
        v = _get_vestibule(vestibule_id, is_member=True, player_id=player_id)
        # Only the leader can create the vestibule
        leader = v.players.get_leader(allow_world=False)
        if leader.uid != player_id:
            raise ValueError('You cannot start this vestibule')
        w = v.start()
        return dict(world=dict(uid=w.uid))