from functools import wraps
from formencode import Invalid
from flask.ext.login import (login_required, login_user, logout_user,
                             current_user)
from flask import (Blueprint, redirect, url_for, flash, render_template,
                   request, g, abort)
from equanimity.player import Player
from server.utils import AttributeDict
from server.forms.users import LoginForm, SignupForm

users = Blueprint('users', __name__, url_prefix='/user')


def home():
    return redirect(url_for('frontend.index'))


def login_unrequired(f):
    @wraps(f)
    def wrapped(*args, **kwargs):
        if not current_user.is_anonymous():
            flash('Currently logged in')
            return home()
        return f(*args, **kwargs)
    return wrapped


@users.route('/signup', methods=['POST', 'GET'])
@login_unrequired
def signup():
    form = SignupForm()
    if request.method == 'GET':
        return render_template('users/signup.html', form=form)
    try:
        form = form.to_python(g.form_data, state=AttributeDict())
    except Invalid as e:
        return render_template('users/signup.html', form=form,
                               errors=e.unpack_errors())
    user = Player(form['username'], form['email'], form['password'])
    login_user(user, remember=True)
    user.login()
    user.persist()
    flash('Created new user "{0}"'.format(user.display_username))
    return home()


@users.route('/login', methods=['POST', 'GET'])
@login_unrequired
def login():
    form = LoginForm()
    if request.method == 'GET':
        return render_template('users/login.html', form=form)
    state = AttributeDict()
    try:
        form = form.to_python(g.form_data, state=state)
    except Invalid as e:
        return render_template('users/login.html', form=form,
                               errors=e.unpack_errors())
    login_user(state.user, remember=True)
    state.user.login()
    flash('Logged in as "{0}"'.format(state.user.display_username))
    return home()


@users.route('/logout')
@login_required
def logout():
    if not current_user.is_anonymous():
        logout_user()
        flash('Logged out successfully')
    return home()
