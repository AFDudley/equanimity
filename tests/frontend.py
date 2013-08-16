from base import FlaskTest


class FrontendTest(FlaskTest):

    def main_page_test(self):
        r = self.get('frontend.index')
        self.assert200(r)
