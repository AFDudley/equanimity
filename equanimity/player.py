"""
player.py

Created by AFD on 2013-08-05.
Copyright (c) 2013 A. Frederick Dudley. All rights reserved.
"""
import operator
from itertools import chain
from persistent import Persistent
from datetime import datetime
from flask.ext.login import UserMixin
from flask import current_app
from const import WORLD_UID
from world import get_world
from server import bcrypt, db


PASSWORD_LEN = dict(max=64, min=8)
EMAIL_LEN = dict(max=256, min=0)
USERNAME_LEN = dict(max=32, min=3)


class Player(Persistent, UserMixin):
    """Object that contains player infomration."""

    @classmethod
    def email_available(cls, email):
        return (cls.get_by_email(email) is None)

    @classmethod
    def username_available(cls, username):
        return (cls.get_by_username(username) is None)

    @classmethod
    def get_by_username(cls, username):
        return db['player_username'].get(username.lower())

    @classmethod
    def get_by_email(cls, email):
        return db['player_email'].get(email.lower())

    @classmethod
    def get(cls, uid):
        try:
            uid = int(uid)
        except Exception:
            msg = 'Invalid user id .get(): {0}'
            current_app.logger.warning(msg.format(uid))
            return
        return db['players'].get(uid)

    def __init__(self, username, email, password):
        Persistent.__init__(self)
        UserMixin.__init__(self)
        self.username = username
        self.email = email
        self.password = password
        self._set_defaults()
        self.uid = db['player_uid'].get_next_id()

    def api_view(self):
        return dict(username=self.name, email=self.email, uid=self.uid)

    def world_view(self, world):
        w = get_world(world)
        if w is None or self.uid not in w.players:
            return {}
        fields = [w.fields[c] for c in self.get_visible_fields(world)]
        return dict(visible_fields=[f.api_view() for f in fields])

    def combatant_view(self, squad):
        """ API data to return when requested as a combatant in a battle """
        return dict(username=self.name, uid=self.uid,
                    squad=squad.combatant_view())

    def get_fields(self, world):
        w = get_world(world)
        return {c: f for c, f in w.fields.iteritems() if f.owner == self}

    def get_visible_fields(self, world_id):
        g = db['grid']
        fields = ([c] + g.get_adjacent(c) for c in self.get_fields(world_id))
        fields = reduce(operator.add, fields, [])
        return set(fields)

    def get_squads(self, world_id):
        squads = (f.stronghold.squads.items.values()
                  for f in self.get_fields(world_id).values())
        return list(chain.from_iterable(squads))

    @property
    def name(self):
        return self.display_username

    @property
    def username(self):
        return self._username

    @username.setter
    def username(self, username):
        self._username = username.lower()
        self.display_username = username

    @property
    def email(self):
        return self._email

    @email.setter
    def email(self, email):
        self._email = email.lower()

    @property
    def password(self):
        return self._password

    @password.setter
    def password(self, password):
        self._password = bcrypt.generate_password_hash(password)

    def check_password(self, password):
        return bcrypt.check_password_hash(self.password, password)

    def persist(self):
        db['players'][self.uid] = self
        db['player_username'][self.username] = self
        db['player_email'][self.email] = self

    def login(self):
        self.last_login = datetime.utcnow()
        self.login_count += 1

    def is_world(self):
        return False

    def __eq__(self, other):
        print other, type(other), self.__class__, other.__class__
        if not isinstance(other, self.__class__):
            return False
        return self.uid == other.uid

    def __ne__(self, other):
        return not self.__eq__(other)

    """ Flask-Login interface
        http://flask-login.readthedocs.org/en/latest/#your-user-class
        Interface methods not defined here are inherited from UserMixin
    """

    def get_id(self):
        return unicode(self.uid)

    def __repr__(self):
        return '<{0}: {1}>'.format(self.__class__.__name__, self.uid)

    def _set_defaults(self):
        self.created_at = datetime.utcnow()
        self.last_login = self.created_at
        self.login_count = 0


class WorldPlayer(Player):

    @classmethod
    def get(cls):
        return db['players'][WORLD_UID]

    def __init__(self):
        Persistent.__init__(self)
        UserMixin.__init__(self)
        self.uid = WORLD_UID
        self.username = 'World'
        self.email = ''
        self._password = ''
        self._set_defaults()

    def persist(self):
        db['players'][self.uid] = self

    def is_world(self):
        return True
