from ..base import FlaskTest
from server import csrf


class FrontendTest(FlaskTest):

    xhr = False

    def main_page_test(self):
        r = self.get('frontend.index')
        self.assert200(r)


class CSRFTest(FlaskTest):

    def setUp(self):
        super(CSRFTest, self).setUp()
        csrf._csrf_disable = False

    def csrf_page_test(self):
        r = self.get('frontend.csrf_token')
        self.assert200(r)
        self.assertIn('token', r.json)
        self.assertTrue(r.json['token'])
