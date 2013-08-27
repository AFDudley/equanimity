"""
player.py

Created by AFD on 2013-08-05.
Copyright (c) 2013 A. Frederick Dudley. All rights reserved.
"""
import transaction
from persistent.mapping import PersistentMapping
from persistent import Persistent
from datetime import datetime
from flask.ext.login import UserMixin
from flask import current_app
from const import WORLD_UID
from server import bcrypt, db


PASSWORD_LEN = dict(max=64, min=8)
EMAIL_LEN = dict(max=256, min=0)
USERNAME_LEN = dict(max=32, min=3)


class Player(Persistent, UserMixin):
    """Object that contains player infomration."""
    def __init__(self, username, email, password, squads=None):
        Persistent.__init__(self)
        self.uid = db['player_uid'].get_next_id()
        self.set_username(username)
        self.set_email(email)
        self.set_password(password)
        self._set_defaults(squads=squads)

    def _set_defaults(self, squads=None):
        self.created_at = datetime.utcnow()
        self.last_login = self.created_at
        self.login_count = 0
        self.reset_world_state(squads=squads)

    def reset_world_state(self, squads=None):
        self.squads = squads
        self.fields = PersistentMapping()
        self.cookie = None
        self.roads = None
        self.treaties = None

    @property
    def name(self):
        return self.display_username

    def set_username(self, username):
        self.username = username.lower()
        self.display_username = username

    def set_email(self, email):
        self.email = email.lower()

    def set_password(self, password):
        self.password = bcrypt.generate_password_hash(password)

    def check_password(self, password):
        return bcrypt.check_password_hash(self.password, password)

    def persist(self):
        db['player'][self.uid] = self
        db['player_username'][self.username] = self
        db['player_email'][self.email] = self
        transaction.commit()

    def login(self):
        self.last_login = datetime.utcnow()
        self.login_count += 1
        transaction.commit()

    def is_world(self):
        return False

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
        return db['player'].get(uid)

    """ Flask-Login interface
        http://flask-login.readthedocs.org/en/latest/#your-user-class
        Interface methods not defined here are inherited from UserMixin
    """

    def get_id(self):
        return unicode(self.uid)

    def __repr__(self):
        return '<{0}: {1}>'.format(self.__class__.__name__, self.uid)


class WorldPlayer(Player):

    def __init__(self):
        Persistent.__init__(self)
        self.uid = WORLD_UID
        self.set_username('World')
        self.email = ''
        self.password = ''
        self._set_defaults()

    def persist(self):
        db['player'][self.uid] = self
        transaction.commit()

    def is_world(self):
        return True
