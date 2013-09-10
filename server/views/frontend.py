from flask import Blueprint, render_template
from server import csrf
from server.decorators import api


frontend = Blueprint('frontend', __name__, url_prefix='')


@frontend.route('/')
def index():
    return render_template('frontend/index.html')


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
