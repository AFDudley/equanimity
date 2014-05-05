import os
import gevent
from flask import (Blueprint, render_template, send_file, stream_with_context,
                   Response, request, json)
from flask.ext.login import login_required, current_user
from server import csrf
from server.decorators import api

from redis import Redis, ConnectionPool
r = Redis(connection_pool=ConnectionPool(host='localhost', port=6379, db=1))

frontend = Blueprint('frontend', __name__, url_prefix='')


@frontend.route('/')
def index():
    gitinfo = ['error\n', 'error\n']
    gi = 'gitinfo.txt'
    if os.path.isfile(gi):
        with open(gi, 'r') as f:
            gitinfo = f.readlines()
    else: print "no file: {0}".format(os.getcwd())
    return render_template('btjs3/client.html', gitinfo=gitinfo)


@frontend.route('/users/login.html')
def login():
    return render_template('users/login.html')


# Serve the js from here until nginx handles the static content
@frontend.route('/js/<path:path>')
def static_proxy(path):
    path = os.path.join('templates/btjs3/js', path)
    return send_file(path)


@stream_with_context
def _stream():
    event = r.pubsub(ignore_subscribe_messages=True)
    #event = r.pubsub()
    pattern = 'user.{}.*'.format(current_user.uid)
    event.psubscribe(pattern)
    pid = os.getpid()
    while True:
        print "server _stream: {}".format(pid)
        message = event.get_message()
        out = '_'
        if message:
            print "event! {0} {1}".format(pid, message)
            yield 'data: ' + json.dumps(message['data']) + '\n\n'
        gevent.sleep(5)


@frontend.route('/events')
@login_required
def stream():
    return Response(_stream(),
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
