import os
from flask import Blueprint, render_template, send_file
from server import csrf
from server.decorators import api


frontend = Blueprint('frontend', __name__, url_prefix='')


@frontend.route('/')
def index():
    return render_template('btjs3/client.html')


# Serve the js from here until nginx handles the static content
@frontend.route('/js/<path:path>')
def static_proxy(path):
    path = os.path.join('templates/btjs3/js', path)
    return send_file(path)


@csrf.include
@frontend.route('/csrf')
@api
def csrf_token():
    """
    Method: GET
    API Fields:
        None
    """
    return dict(token=csrf._get_token())
