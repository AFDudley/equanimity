from functools import wraps
from flask.ext.login import current_user
from equanimity.stronghold import Stronghold
from equanimity.units import Unit
from equanimity.battle import Game
from equanimity.field import Field
from equanimity.worldtools import get_world as _get_world


def get_thing(cls, ids, name=None, check_owner=True):
    if name is None:
        name = cls.__name__
    thing = cls.get(*ids)
    if thing is None:
        ids = [getattr(id, 'uid', id) for id in ids]
        raise ValueError('Invalid {name} {ids}'.format(name=name, ids=ids))
    if check_owner and thing.owner != current_user._get_current_object():
        raise ValueError('You do not own this {name}'.format(name=name))
    return thing


def unpack_world(f):
    @wraps(f)
    def wrapped(world_id, *args, **kwargs):
        return f(get_world(world_id), *args, **kwargs)
    return wrapped


def get_world(world_id, **kwargs):
    w = _get_world(world_id)
    if w is None:
        raise ValueError('Unknown world {0}'.format(world_id))
    if not w.players.has(current_user._get_current_object()):
        raise ValueError('You are not in this world')
    return w


@unpack_world
def get_field(world, field_location, **kwargs):
    # TODO -- make sure field is visible for the requesting user
    kwargs['check_owner'] = False
    return get_thing(Field, (world, field_location), **kwargs)


@unpack_world
def get_stronghold(world, field_location, **kwargs):
    return get_thing(Stronghold, (world, field_location), **kwargs)


@unpack_world
def get_battle(world, field_location, check_owner=True, **kwargs):
    kwargs['check_owner'] = False
    battle = get_thing(Game, (world, field_location), **kwargs)
    user = current_user._get_current_object()
    if (battle is not None and battle.defender != user and check_owner and
            battle.attacker != user):
        raise ValueError('You are not involved this battle')
    return battle


def get_unit(uid, **kwargs):
    return get_thing(Unit, (uid,), **kwargs)
