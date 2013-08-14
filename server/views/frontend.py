from flask import Blueprint

frontend = Blueprint('frontend', __name__, url_prefix='')


@frontend.route('/')
def index():
    return 'Equanimity'
