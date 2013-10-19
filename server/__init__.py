import os
import logging
from formencode.htmlfill import render as render_form
from flask.ext.seasurf import SeaSurf
from flask.ext.zodb import ZODB
from flask.ext.bcrypt import Bcrypt
from flask.ext.login import LoginManager
from flask.ext.jsonrpc import JSONRPC
from flask import Flask, g, Blueprint


""" ZODB """
db = ZODB()

""" JSONRPC """
jsonrpc = JSONRPC(service_url='/api')

""" Bcrypt """
bcrypt = Bcrypt()

""" Login """
login_manager = LoginManager()

""" CSRF """
csrf = SeaSurf()


def setup_login_manager(app):
    login_manager.login_view = 'users.login'
    login_manager.refresh_view = 'users.login'
    login_manager.session_protection = 'strong'
    login_manager.init_app(app)

    from equanimity.player import Player

    @login_manager.user_loader
    def load_user(uid):
        return Player.get(uid)


def register_blueprints(app):
    from views.frontend import frontend
    from views.users import users
    from rpc.stronghold import stronghold
    from rpc.battle import battle
    from rpc.info import info
    app.register_blueprint(frontend)
    app.register_blueprint(users)
    app.register_blueprint(stronghold)
    app.register_blueprint(battle)
    app.register_blueprint(info)
    rpc_bp = Blueprint('jsonrpc', __name__, url_prefix='/api')
    jsonrpc.register_blueprint(rpc_bp)


def load_config(app, subdomain, config=None):
    if config is not None:
        app.config.from_object('config.{0}'.format(config))
    elif 'EQUANIMITY_SERVER_SETTINGS' in os.environ:
        app.config.from_envvar('EQUANIMITY_SERVER_SETTINGS')
    else:
        app.config.from_object('config.dev')

    if subdomain:
        server_name = subdomain + '.' + app.config['SERVER_NAME']
        app.config['SERVER_NAME'] = server_name

    # make sure STATIC_ROOT is of the correct form
    # This is for hosting static content on a separate domain or sub-url
    static_root = app.config.get('STATIC_ROOT')
    if static_root:
        from server.utils import construct_full_url
        app.config['STATIC_ROOT'] = construct_full_url(static_root)


def inject_context_processors(app):
    @app.context_processor
    def inject_template_globals():
        return dict(render_form=render_form)


def attach_before_request_handlers(app):
    @app.before_request
    def set_defaults():
        g.api_data = None


def attach_loggers(app):
    log_format = ('%(asctime)s [%(pathname)s:%(lineno)d:%(levelname)s] '
                  '%(message)s')
    app.debug_log_format = log_format
    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(logging.Formatter(log_format))
    loggers = ['ZEO']
    loggers = [logging.getLogger(log) for log in loggers]
    if not app.config['DEBUG']:
        loggers.append(app.logger)
    for logger in loggers:
        logger.addHandler(stream_handler)
        logger.setLevel(logging.WARNING)
    if app.config['DEBUG'] or app.config.get('DEBUG_LOGGING'):
        app.logger.setLevel(logging.DEBUG)
    else:
        app.logger.setLevel(logging.INFO)


def create_app(subdomain='', config=None):

    """ App """
    app = Flask(__name__)

    """ Config """
    load_config(app, subdomain, config=config)

    """ Logging """
    attach_loggers(app)

    """ ZODB """
    db.init_app(app)

    """ JSONRPC """
    jsonrpc.init_app(app)

    """ Bcrypt """
    bcrypt.init_app(app)

    """ CSRF """
    csrf.init_app(app)

    """ Login """
    setup_login_manager(app)

    """ Blueprints """
    register_blueprints(app)

    """ Templates """
    inject_context_processors(app)

    """ Request management """
    attach_before_request_handlers(app)

    return app
