import transaction
from functools import wraps
from flask import g, current_app, request, jsonify, abort
from flask.ext.login import current_user
from formencode import variabledecode, Invalid as InvalidSchema
from server.utils import api_error, RateLimit


def api(f):
    """ API endpoint decorator
    Unpacks both content-type: json and formdata as needed, in addition
    to multipart data (files), placing it into g.api_data
    Any form schema errors are caught and packaged into a json error response
    Otherwise, the return value of the wrapped function are packed into a json
    response
    """
    f.api = True

    @wraps(f)
    def wrapped(*args, **kwargs):
        if request.json is not None:
            g.api_data = request.json
        else:
            try:
                g.api_data = variabledecode.variable_decode(request.form)
            except ValueError:
                abort(400)
        file_data = {}
        for name, upload in request.files.items():
            file_data[name] = upload
        file_data = variabledecode.variable_decode(file_data)
        g.api_data.update(file_data)
        try:
            resp = f(*args, **kwargs)
        except InvalidSchema as e:
            resp = api_error(e.unpack_errors())
        code = 200
        if isinstance(resp, tuple):
            resp, code = resp
        if hasattr(resp, 'api_view'):
            resp = resp.api_view()
        try:
            return jsonify(**resp), code  # dict response
        except TypeError:
            try:
                return jsonify(resp), code    # else string, list
            except Exception:
                msg = 'API view response value failed to serialize. Value: {0}'
                current_app.logger.error(msg.format(resp))
                abort(500)
    return wrapped


def script(*create_app_args, **create_app_kwargs):
    """ Wraps a function intended to be run as a script (not through a request)
    Example use:

    @script
    def do_thing():
        from server import db
        print list(db['players'])
    """
    from server import create_app

    def _script(f):
        '''Calls the decorated function with a request context bound'''
        @wraps(f)
        def wrapped(*args, **kwargs):
            app = create_app(*create_app_args, **create_app_kwargs)
            with app.test_request_context():
                app.preprocess_request()
                return f(*args, **kwargs)
        return wrapped
    return _script


def _on_over_limit(limit):
    return jsonify(dict(message='You hit the rate limit')), 400


def ratelimit(limit, per=300, over_limit=_on_over_limit,
              scope_func=lambda: request.remote_addr,
              key_func=lambda: request.endpoint):
    # http://flask.pocoo.org/snippets/70/
    def decorator(f):
        @wraps(f)
        def rate_limited(*args, **kwargs):
            key = '%s/%s' % (key_func(), scope_func())
            rlimit = RateLimit(key, limit, per)
            g._view_rate_limit = rlimit
            if over_limit is not None and rlimit.over_limit:
                return over_limit(rlimit)
            return f(*args, **kwargs)
        return rate_limited
    return decorator


def require_login(f):
    """The official one is flask.ext.login.login_required, but that doesn't
    work with any json-rpc endpoints. This one does, as long as the decorator
    is applied after the @rpc decorator
    """
    @wraps(f)
    def wrapped(*args, **kwargs):
        if not current_user.is_active():
            abort(401)
        return f(*args, **kwargs)
    return wrapped


def commit(f):
    """ Commits to zodb after the decorated function has been
    called
    """
    @wraps(f)
    def wrapped(*args, **kwargs):
        r = f(*args, **kwargs)
        transaction.commit()
        return r
    return wrapped
