#!/usr/bin/env python
from common import hack_syspath
hack_syspath(__file__)
from argparse import ArgumentParser
from flask import current_app, url_for
from server.decorators import script


def get_args():
    p = ArgumentParser(prog='Equanimity')
    s = p.add_subparsers()
    p_user = s.add_parser('user', help='User account management')
    s_user = p_user.add_subparsers()

    """ ./client.py user create """
    p_user_create = s_user.add_parser('create', help='Create user')
    p_user_create.add_argument('username')
    p_user_create.add_argument('password')
    p_user_create.add_argument('email')
    p_user_create.set_defaults(func=create_user)

    return p.parse_args()


def _convert_args_to_dict(args):
    d = {}
    d.update(args.__dict__)
    return d


@script()
def create_user(username, password, email):
    client = current_app.test_client()
    data = dict(username=username, password=password, email=email)
    r = client.post(url_for('users.signup'), data=data)
    if r.status_code == 200:
        print 'Created user'
    else:
        print 'Failed to create user'
    print r.data


def run_command(args):
    args = _convert_args_to_dict(args)
    args.pop('func')(**args)


if __name__ == '__main__':
    args = get_args()
    run_command(args)
