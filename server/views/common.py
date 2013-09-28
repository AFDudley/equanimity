from flask.ext.login import current_user
from equanimity.stronghold import Stronghold
from equanimity.units import Unit
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
    kwargs['check_owner'] = False
    return get_thing(Field, field_location, **kwargs)
