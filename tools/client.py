#!/usr/bin/env python

from common import hack_syspath
hack_syspath(__file__)
import requests
from uuid import uuid1
from argparse import ArgumentParser
from flask import json
from flask.ext.jsonrpc.proxy import ServiceProxy
from urlparse import urljoin


""" Example CLI Usage:

./client.py <username> <password> <action> <args...>

All args are eval'd to convert to the correct python type. This affects how
you type the args. The quotes are necessary because of the shell.

Lists: "[0,1]"
Tuples: "(0,1)"
Dictionaries: "{'arg':7}"
Strings: "'a_word'"
Integers: 5
Floats: 0.5

Creating an account:
./client.py myusername mypassword signup myemail@email.com

Performing an action:
./client.py myusername mypassword form_squad "[0,0]" "[0,1,4]"
./client.py myusername mypassword name_squad "[0,0]" 2 "'squadname'"

"""


class ClientServiceProxy(ServiceProxy):

    def _make_payload(self, params):
        return json.dumps({
            'jsonrpc': self.version,
            'method': self.service_name.strip('.'),
            'params': params,
            'id': str(uuid1())
        })

    def send_payload(self, params, **kwargs):
        return requests.post(self.service_url, data=self._make_payload(params),
                             **kwargs)

    def __call__(self, params, **kwargs):
        resp = self.send_payload(params, **kwargs)
        try:
            return resp.json()
        except ValueError:
            return resp.content


class EquanimityClient(object):

    def __init__(self, url='http://127.0.0.1:5000', service_name=''):
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


def print_result(r):
    if r.get('error'):
        print r['error']['message']
    else:
        print r['result']


def get_args():
    p = ArgumentParser(prog='Equanimity')
    p.add_argument('--config', default='dev', help='Server config file to use')

    p.add_argument('--url', default='http://127.0.0.1:5000/',
                   help='URL of server')
    p.add_argument('username', help='User to perform action as')
    p.add_argument('password', help='Password for user authentication')
    p.add_argument('method', help='Name of rpc method')
    p.add_argument('params', nargs='*', help='Rpc method parameters')
    return p.parse_args()


def process_args(args):
    # We need to convert the argument strings to native data types
    args.params = map(eval, args.params)
    c = EquanimityClient(args.url)
    if args.method == 'signup':
        if not args.params:
            print 'Must provide email for signup'
        else:
            print c.signup(args.username, args.password, args.params[0]).json()
    else:
        c.login(args.username, args.password)
        print_result(c.rpc(args.method, args.params))


if __name__ == '__main__':
    process_args(get_args())
