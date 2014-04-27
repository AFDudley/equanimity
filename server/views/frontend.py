import os
from flask import (Blueprint, render_template, send_file, stream_with_context,
                   Response, json)
from flask.ext.login import login_required, current_user
from server import csrf
from server.decorators import api

from redis import Redis, ConnectionPool
r = Redis(connection_pool=ConnectionPool(host='localhost', port=6379, db=1))

frontend = Blueprint('frontend', __name__, url_prefix='')


@frontend.route('/')
def index():
    return render_template('btjs3/client.html')


@frontend.route('/users/login.html')
def login():
    return render_template('users/login.html')


# Serve the js from here until nginx handles the static content
@frontend.route('/js/<path:path>')
def static_proxy(path):
    path = os.path.join('templates/btjs3/js', path)
    return send_file(path)


@frontend.route('/events')
@login_required
def stream():
    event = r.pubsub()
    event.psubscribe('user.{}.*'.format(current_user.uid))
    listener = event.listen()
    def events():
        print "server _stream"
        yield 'data: ' + json.dumps(listener.next()) + '\n\n'
    return Response(stream_with_context(events()),
                    mimetype='text/event-stream',
                    headers={'Cache-Control': 'no-cache',
                             'Connection': 'keep-alive'})


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
