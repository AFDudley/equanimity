from mock import patch
from unittest import TestCase
from flask import url_for
from equanimity.helpers import AttributeDict
from tools.client import EquanimityClient, get_args, process_args
from server import create_app


class ArgsTest(TestCase):

    """ Calls the methods that process arguments to ensure cli usage doesn't
    crash """

    @patch('tools.client.EquanimityClient.signup')
    def test_process_args_signup(self, mock_signup):
        args = AttributeDict(url='http://eqq.com', method='signup',
                             username='xxx', password='x' * 9,
                             params=['"test@gmail.com"'])
        process_args(args)
        mock_signup.assert_called_with(args.username, args.password,
                                       args.params[0])

    @patch('tools.client.EquanimityClient.login')
    @patch('tools.client.EquanimityClient.rpc')
    def test_process_args_rpc(self, mock_rpc, mock_login):
        args = AttributeDict(url='http://eqq.com', method='name_squad',
                             username='xxx', password='x' * 9,
                             params=['[0, 0]', '0', '"mysquad"'])
        process_args(args)
        mock_login.assert_called_with(args.username, args.password)
        mock_rpc.assert_called_with(args.method, *args.params)

    def test_get_args(self):
        try:
            get_args()
        except SystemExit:
            pass


class EquanimityClientTest(TestCase):

    def setUp(self):
        super(EquanimityClientTest, self).setUp()
        self.url = 'http://eqq.com'
        self.service_name = 'yyy'
        self.c = EquanimityClient(url=self.url, service_name=self.service_name)

    def url_for(self, endpoint):
        with create_app(config='test').test_request_context():
            return url_for(endpoint)

    def test_create(self):
        self.assertEqual(self.c.url, self.url)
        self.assertEqual(self.c.cookies, {})
        self.assertEqual(self.c.proxy.service_url, self.url + '/api')
        self.assertEqual(self.c.proxy.service_name, self.service_name)

    def test_create_with_defaults(self):
        self.c = EquanimityClient()
        self.assertEqual(self.c.url, 'http://127.0.0.1:5000')
        self.assertEqual(self.c.cookies, {})
        self.assertEqual(self.c.proxy.service_url, 'http://127.0.0.1:5000/api')
        self.assertEqual(self.c.proxy.service_name, '')

    def test_clear_cookies(self):
        self.c.cookies = dict(token='xxx')
        self.c.clear_cookies()
        self.assertEqual(self.c.cookies, {})

    @patch.object(EquanimityClient, '_post')
    def test_signup(self, mock_post):
        url = self.url + self.url_for('users.signup')
        data = AttributeDict(username='dog', password='x' * 9,
                             email='dog@gmail.com')
        self.c.signup(data.username, data.password, data.email)
        mock_post.assert_called_with(url, data=dict(data))

    @patch.object(EquanimityClient, '_post')
    def test_login(self, mock_post):
        url = self.url + self.url_for('users.login')
        args = AttributeDict(username='dog', password='x' * 9)
        self.c.login(args.username, args.password)
        mock_post.assert_called_with(url, data=dict(args))

    @patch.object(EquanimityClient, '_get')
    def test_logout(self, mock_get):
        url = self.url + self.url_for('users.logout')
        self.c.logout()
        mock_get.assert_called_with(url)

    @patch('tools.client.ClientServiceProxy.send_payload')
    def test_rpc(self, mock_send_payload):
        resp = 2
        mock_send_payload.return_value = AttributeDict(json=lambda: resp)
        self.c.cookies = dict(token='xxx')
        params = (0, 'string', [1, 2])
        method = 'stronghold.name_unit'
        r = self.c.rpc(method, *params)
        self.assertEqual(r, resp)
        mock_send_payload.assert_called_with(params, cookies=self.c.cookies)

    @patch('tools.client.ClientServiceProxy.send_payload')
    def test_rpc_no_json_response(self, mock_send_payload):
        resp = 2
        # int('a') will raise ValueError, forcing it to return content
        mock_send_payload.return_value = AttributeDict(json=lambda: int('a'),
                                                       content=resp)
        self.c.cookies = dict(token='xxx')
        params = (0, 'string', [1, 2])
        method = 'stronghold.name_unit'
        r = self.c.rpc(method, *params)
        self.assertEqual(r, resp)
        mock_send_payload.assert_called_with(params, cookies=self.c.cookies)

    @patch('tools.client.grequests.post')
    def test_rpc_service_name(self, mock_post):
        resp = 2
        mock_post.return_value = AttributeDict(json=lambda: resp)
        mock_post.return_value.send = lambda *args: mock_post.return_value
        self.c.cookies = dict(token='xxx')
        params = (0, 'string', [1, 2])
        method = 'stronghold.name_unit'
        r = self.c.rpc(method, *params)
        self.assertEqual(r, resp)
        # Make sure the service name is correctly concatenated
        service_name = '.'.join([self.service_name, method])
        self.assertIn(service_name, mock_post.call_args[1]['data'])

    @patch('tools.client.grequests.post')
    def test_post(self, mock_post):
        resp = AttributeDict(cookies=dict(token=88))
        mock_post.return_value = resp
        self.c.cookies = dict(csrf='yyy')
        resp.send = lambda *args: resp
        r = self.c._post(self.url, cookies=dict(token='xxx'))
        self.assertEqual(r, resp)
        self.assertEqual(self.c.cookies, resp.cookies)
        mock_post.assert_called_with(self.url, cookies=dict(token='xxx',
                                                            csrf='yyy'))

    @patch('tools.client.grequests.get')
    def test_get(self, mock_get):
        resp = AttributeDict(cookies=dict(token=77))
        mock_get.return_value = resp
        self.c.cookies = dict(csrf='yyy')
        resp.send = lambda *args: resp
        r = self.c._get(self.url, cookies=dict(token='xxx'))
        self.assertEqual(r, resp)
        self.assertEqual(self.c.cookies, resp.cookies)
        mock_get.assert_called_with(self.url, cookies=dict(token='xxx',
                                                           csrf='yyy'))
