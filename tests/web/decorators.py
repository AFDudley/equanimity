from unittest import TestCase
from mock import patch
from os import urandom
from StringIO import StringIO
from flask import Blueprint, url_for
from equanimity.world import init_db
from server import db, create_app
from server.decorators import script, api, ratelimit, commit
from users import UserTestBase
from ..base import FlaskTest


class APIDecoratorTest(UserTestBase):

    def setUp(self):
        super(APIDecoratorTest, self).setUp()
        self.create_user()
        self.logout()

    def test_content_type_json(self):
        self.login(use_json=True, check_status=True)

    @patch('server.decorators.variabledecode.variable_decode')
    def test_failed_variabledecode(self, mock_decode):
        mock_decode.side_effect = ValueError
        r = self.login(use_json=False, check_status=False)
        self.assert400(r)

    def test_upload_file(self):
        pass


class APIResponseProcessorTest(TestCase):

    def test_non_jsonifiable_return_value(self):
        app = create_app(config='test')
        bad = Blueprint('test', __name__, url_prefix='/test')

        @bad.route('/hey')
        @api
        def bad_view():
            return ['hey']

        app.register_blueprint(bad)
        client = app.test_client()
        with app.test_request_context('/'):
            url = url_for('test.bad_view')
        r = client.get(url)
        self.assertEqual(r.status_code, 500)

    def test_api_status_code_handling(self):
        app = create_app(config='test')
        b = Blueprint('test', __name__, url_prefix='/test')

        @b.route('/')
        @api
        def status_return():
            return dict(msg='ok'), 666

        app.register_blueprint(b)
        client = app.test_client()
        with app.test_request_context('/'):
            url = url_for('test.status_return')
        r = client.get(url)
        self.assertEqual(r.status_code, 666)


class FileUploadTest(FlaskTest):

    xhr = False

    @property
    def filedata(self):
        return (StringIO(urandom(64)), 'xxx.png')

    def test_file_upload(self):
        r = self.post('users.login', data=dict(image=self.filedata))
        self.assert200(r)


class ScriptDecoratorTest(TestCase):

    def test_wrapped_script(self):
        @script(config='test')
        def test():
            init_db(reset=True)
            self.assertIn('players', db)
        test()


class RateLimitDecoratorTest(TestCase):

    def setUp(self):
        super(RateLimitDecoratorTest, self).setUp()
        self.app = create_app(config='test')
        with self.app.test_request_context():
            init_db(reset=True)
        self.b = Blueprint('test', __name__, url_prefix='/test')

    def test_rate_limit_decorator(self):
        limit = 5

        @self.b.route('/')
        @ratelimit(limit, per=10000)
        def test():
            return 'OK'

        self.app.register_blueprint(self.b)
        client = self.app.test_client()
        with self.app.test_request_context('/'):
            url = url_for('test.test')

        for i in xrange(limit - 1):
            r = client.get(url)
            self.assertEqual(r.status_code, 200)
            self.assertIn('OK', r.data)

        r = client.get(url)
        self.assertEqual(r.status_code, 400)
        self.assertIn('hit the rate limit', r.data)


class CommitTest(TestCase):

    @patch('server.decorators.transaction.commit')
    def test_commit(self, mock_commit):
        f = lambda: 7
        g = commit(f)
        self.assertEqual(g(), 7)
        mock_commit.assert_called_once_with()
