#!/usr/bin/env python
from common import hack_syspath
hack_syspath(__file__)
from argparse import ArgumentParser
from flask import current_app, url_for
from equanimity.player import Player
from server import db
from server.decorators import script


import requests
from flask import json
from flask.ext.jsonrpc import ServiceProxy
from urlparse import urljoin


class ClientServiceProxy(ServiceProxy):

    def send_payload(self, params, **kwargs):
        return requests.post(self.service_url, data=json.dumps(params),
                             **kwargs)

    def __call__(self, params, **kwargs):
        resp = self.send_payload(params, **kwargs)
        return resp.json()


class EquanimityClient(object):

    def __init__(self, url='http://127.0.0.1:5000', service_name='equanimity'):
        self.url = url
        self.proxy = ClientServiceProxy(urljoin(url, '/api'),
                                        service_name=service_name)
        self.clear_cookies()

    def clear_cookies(self):
        self.cookies = {}

    def signup(self, username, password, email):
        url = urljoin(self.url, '/auth/signup')
        data = dict(username=username, password=password, email=email)
        return self._post(url, data=data)

    def login(self, username, password):
        url = urljoin(self.url, '/auth/login')
        data = dict(username=username, password=password)
        return self._post(url, data=data)

    def logout(self):
        url = urljoin(self.url, '/auth/logout')
        return self._get(url)

    def rpc(self, method, params):
        methods = method.split('.')
        action = self.proxy
        for m in methods:
            action = getattr(action, m)
        return action(params, cookies=self.cookies)

    def _post(self, *args, **kwargs):
        kwargs.setdefault('cookies', {}).update(self.cookies)
        r = requests.post(*args, **kwargs)
        self.cookies = dict(r.cookies)
        return r

    def _get(self, *args, **kwargs):
        kwargs.setdefault('cookies', {}).update(self.cookies)
        r = requests.get(*args, **kwargs)
        self.cookies = dict(r.cookies)
        return r


def get_args():
    p = ArgumentParser(prog='Equanimity')
    p.add_argument('--config', default='dev', help='Server config file to use')
    s = p.add_subparsers()
    p_user = s.add_parser('user', help='User account management')
    s_user = p_user.add_subparsers()

    """ ./client.py user create """
    p_user_create = s_user.add_parser('create', help='Create user')
    p_user_create.add_argument('username')
    p_user_create.add_argument('password')
    p_user_create.add_argument('email')
    p_user_create.set_defaults(func=create_user)

    """ ./client.py user show """
    p_user_show = s_user.add_parser('show', help='Show user info')
    p_user_show.add_argument('username')
    p_user_show.set_defaults(func=show_user)

    """ ./client.py user list """
    p_user_list = s_user.add_parser('list', help='List users')
    p_user_list.add_argument('--limit', default=20, type=int,
                             help='How many to show')
    p_user_list.add_argument('--offset', default=0, type=int,
                             help='Offset from where to begin listing')
    p_user_list.set_defaults(func=show_users)

    return p.parse_args()


def create_user(username, password, email):
    client = current_app.test_client()
    data = dict(username=username, password=password, email=email)
    r = client.post(url_for('users.signup'), data=data)
    if r.status_code == 200:
        data = json.loads(r.data)
        if not data.get('errors', ''):
            print 'Created user'
        else:
            print 'Failed to create user'
    else:
        print 'Error while creating user'
    print r.data


def show_user(username):
    p = Player.get_by_username(username)
    if p is None:
        print 'Player "{0}" not found'.format(username)
    else:
        print p


def show_users(limit, offset):
    found = False
    for i in range(offset, offset + limit):
        if i in db['players']:
            print db['players'][i]
            found = True
    if not found:
        print 'No player found for this range'


def run_command(args):
    args = dict(**args.__dict__)
    config = args.pop('config')
    func = script(config=config)(args.pop('func'))
    return func(**args)


if __name__ == '__main__':
    args = get_args()
    run_command(args)
