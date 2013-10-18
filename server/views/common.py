from flask.ext.login import current_user
from equanimity.stronghold import Stronghold
from equanimity.units import Unit
from equanimity.battle import Game
from equanimity.field import Field


def get_thing(cls, uid, name=None, check_owner=True):
    if name is None:
        name = cls.__name__
    thing = cls.get(uid)
    if thing is None:
        raise ValueError('Invalid {name} {uid}'.format(name=name, uid=uid))
    if check_owner and thing.owner != current_user:
        raise ValueError('You do not own this {name}'.format(name=name))
    return thing


def get_stronghold(field_location, **kwargs):
    return get_thing(Stronghold, field_location, **kwargs)


def get_unit(uid, **kwargs):
    return get_thing(Unit, uid, **kwargs)


def get_field(field_location, **kwargs):
    # TODO -- make sure field is visible for the requesting user
    kwargs['check_owner'] = False
    return get_thing(Field, field_location, **kwargs)


def get_battle(field_location, check_owner=True, **kwargs):
    kwargs['check_owner'] = False
    battle = get_thing(Game, field_location, **kwargs)
    if (check_owner and battle.defender != current_user and
            battle.attacker != current_user):
        raise ValueError('You are not involved this battle')
    return battle
