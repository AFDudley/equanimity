import os.path
from datetime import datetime

from flask.ext.bcrypt import Bcrypt
from flask.ext.login import LoginManager
from flask import Flask


""" Bcrypt """
bcrypt = Bcrypt()

""" Login """
login_manager = LoginManager()
login_manager.login_view = 'players.login'
login_manager.refresh_view = 'players.login'
login_manager.session_protection = 'strong'


def register_blueprints(app):
    from views.frontend import frontend
    app.register_blueprint(frontend)


def load_config(app, subdomain):
    if os.environ.get('EQUANIMITY_SERVER_SETTINGS') is not None:
        app.config.from_envvar('EQUANIMITY_SERVER_SETTINGS')
    else:
        app.config.from_object('config.dev')

    if subdomain:
        server_name = subdomain + '.' + app.config['SERVER_NAME']
        app.config['SERVER_NAME'] = server_name

    # make sure STATIC_ROOT is of the correct form
    static_root = app.config.get('STATIC_ROOT')
    if static_root:
        from gweb.utils import construct_full_url
        app.config['STATIC_ROOT'] = construct_full_url(static_root)


def create_app(subdomain=''):

    """ App """
    app = Flask(__name__)

    """ Config """
    load_config(app, subdomain)

    """ Bcrypt """
    bcrypt.init_app(app)

    """ Login """
    login_manager.init_app(app, add_context_processor=True)

    """ Blueprints """
    register_blueprints(app)

    return app
