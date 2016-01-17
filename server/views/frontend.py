import os
from flask import Blueprint, render_template, send_file
from server import csrf
from server.decorators import api


frontend = Blueprint('frontend', __name__, url_prefix='')


@frontend.route('/')
def index():
    gitinfo = ['error\n', 'error\n']
    gi = 'gitinfo.txt'
    if os.path.isfile(gi):
        with open(gi, 'r') as f:
            gitinfo = f.readlines()
    else:
        print "no file: {0}".format(os.getcwd())
    return render_template('btjs3/client.html', gitinfo=gitinfo)


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
