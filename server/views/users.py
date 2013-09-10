from flask.ext.login import (login_required, login_user, logout_user,
                             current_user)
from flask import Blueprint, redirect, url_for, g
from equanimity.player import Player
from server.utils import AttributeDict
from server.forms.users import LoginForm, SignupForm
from server.decorators import api

users = Blueprint('users', __name__, url_prefix='/api/user')


def home():
    return redirect(url_for('frontend.index'))


@users.route('/signup', methods=['POST'])
@api
def signup():
    """ Methods: POST
    Fields:
        username
        email
        password
    Return:
        user json
    """
    form = SignupForm().to_python(g.form_data, state=AttributeDict())
    user = Player(form['username'], form['email'], form['password'])
    login_user(user, remember=True)
    user.login()
    user.persist()
    return user


@users.route('/login', methods=['POST'])
@api
def login():
    """ Method: POST
    Fields:
        username
        password
    Return:
        user json
    """
    state = AttributeDict()
    LoginForm().to_python(g.form_data, state=state)
    login_user(state.user, remember=True)
    state.user.login()
    return state.user


@users.route('/logout')
@login_required
@api
def logout():
    """ Method: GET
    Fields:
        None
    Returns:
        uid of player logged out
    """
    uid = current_user.uid
    logout_user()
    return dict(uid=uid)


@users.route('/me')
@login_required
@api
def me():
    return current_user
