from flask import Blueprint, render_template

frontend = Blueprint('frontend', __name__, url_prefix='')


@frontend.route('/')
def index():
    return render_template('frontend/index.html')
