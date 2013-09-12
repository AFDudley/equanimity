from equanimity.player import Player
from tools.client import (create_user, show_user, show_users, run_command,
                          get_args)
from base import FlaskTestDB


class ClientTest(FlaskTestDB):

    def test_run_command(self):

        class Args(object):
            def __init__(self):
                self.username = 'dog'
                self.func = lambda username: username
                self.config = 'test'

        self.assertEqual(run_command(Args()), 'dog')

    def test_get_args(self):
        try:
            get_args()
        except SystemExit:
            pass


class UserClientTest(FlaskTestDB):

    """
    These don't have much to test since its mostly printing to stdout,
    but have the methods run so we know they aren't crashing on expected
    input
    """

    def test_create_user(self):
        create_user('dog', 'x' * 10, 'dog@gmail.com')
        self.assertTrue(Player.get_by_username('dog'))
        create_user('cat', 'x', 'cat@gmail.com')
        self.assertIs(Player.get_by_username('cat'), None)

    def test_show_user(self):
        create_user('dog', 'x' * 10, 'dog@gmail.com')
        show_user('dog')
        show_user('xxx')

    def test_show_users(self):
        show_users(10, 0)
        create_user('dog', 'x' * 10, 'dog@gmail.com')
        show_users(10, 0)
