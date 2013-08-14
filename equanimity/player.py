"""
player.py

Created by AFD on 2013-08-05.
Copyright (c) 2013 A. Frederick Dudley. All rights reserved.
"""
from persistent.mapping import PersistentMapping
from persistent import Persistent
from flask.ext.login import UserMixin
from server import bcrypt, db


PASSWORD_LEN = dict(max=64, min=8)
EMAIL_LEN = dict(max=256, min=0)
USERNAME_LEN = dict(max=32, min=3)


class Player(Persistent, UserMixin):
    """Object that contains player infomration."""
    def __init__(self, username, email, password, squads=None):
        Persistent.__init__(self)
        self.set_username(username)
        self.set_email(email)
        self.set_password(password)
        self.squads = squads
        self.Fields = PersistentMapping()
        self.cookie = None
        self.roads = None
        self.treaties = None

    def set_username(self, username):
        self.username = username.lower()
        self.display_username = username

    def set_email(self, email):
        self.email = email.lower()

    def set_password(self, password):
        self.password = bcrypt.generate_password_hash(password)

    def check_password(self, password):
        return bcrypt.check_password_hash(self.password, password)

    """ Flask-Login interface
        http://flask-login.readthedocs.org/en/latest/#your-user-class
        Interface methods not defined here are inherited from UserMixin
    """

    def get_id(self):
        # TODO -- unique id for player?
        return unicode(self.username)


    @classmethod
    def email_available(cls):
        # TODO --
        return True

    @classmethod
    def username_available(cls):
        # TODO --
        return True

    @classmethod
    def get_by_username(cls, username):
        # TODO --
        return None

    @classmethod
    def get(cls, uid):
        # TODO --
        return None
