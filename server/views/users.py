from flask.ext.login import (login_required, login_user, logout_user,
                             current_user)
from flask import (Blueprint, redirect, url_for, flash, render_template,
                   request)
from server.forms.users import LoginForm, SignupForm

users = Blueprint('users', __name__, url_prefix='/user')


def home():
    return redirect(url_for('users.index'))


@users.route('/signup', methods=['POST', 'GET'])
def signup():
    form = SignupForm()
    if request.method == 'GET':
        return render_template('users/signup.html', form=form)
    if not form.validate_on_submit():
        return render_template('users/login.html', form=form)
    flash('Created new user "{0}"'.format(form.user.display_username))
    return home()


@users.route('/login', methods=['POST', 'GET'])
def login():
    if current_user.is_active():
        flash('Already logged in')
        return home()
    form = LoginForm()
    if request.method == 'GET':
        return render_template('users/login.html', form=form)
    if not form.validate_on_submit():
        return render_template('users/login.html', form=form)
    flash('Logged in as {0}'.format(form.user.display_username))
    return home()


@users.route('/logout')
@login_required
def logout():
    if not current_user.is_anonymous():
        logout_user()
        flash('Logged out successfully')
    return home()
