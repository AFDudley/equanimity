from base import FlaskTestDB


class UserTestBase(FlaskTestDB):

    def setUp(self):
        super(UserTestBase, self).setUp()
        self.email = 'test@gmail.com'
        self.username = 'testuserX'
        self.password = 'testtest'
        self.uid = 1

    def get_create_user_data(self):
        return dict(username=self.username, password=self.password,
                    email=self.email)

    def get_login_user_data(self):
        data = self.get_create_user_data()
        del data['email']
        return data

    def create_user(self):
        r = self.post('users.signup', data=self.get_create_user_data())
        self.assert200(r)
        return r

    def logout(self):
        r = self.get('users.logout')
        self.assert200(r)
        return r

    def login(self):
        r = self.post('users.login', data=self.get_login_user_data())
        self.assert200(r)
        return r

    def assertUserExists(self):
        users = [self.db['player_username'][self.username.lower()],
                 self.db['player_email'][self.email.lower()],
                 self.db['player'][self.uid]]
        for user in users:
            self.assertEqual(user.uid, 1)
            self.assertEqual(user.username, self.username.lower())
            self.assertEqual(user.display_username, self.username)
            self.assertEqual(user.email, self.email)
            self.assertTrue(user.password)

    def assertLoggedIn(self):
        r = self.get('frontend.index')
        self.assert200(r)
        self.assertIn(self.username, r.data)
        self.assertIn('Logout', r.data)

    def assertNotLoggedIn(self):
        r = self.get('frontend.index')
        self.assert200(r)
        self.assertNotIn(self.username, r.data)
        self.assertNotIn('Logout', r.data)
        self.assertIn('Login', r.data)
        self.assertIn('Signup', r.data)


class SignupTest(UserTestBase):

    def test_signup(self):
        self.create_user()
        self.assertUserExists()
        self.assertLoggedIn()


class LoginTest(UserTestBase):

    def setUp(self):
        super(LoginTest, self).setUp()
        self.create_user()

    def test_login(self):
        self.assertUserExists()
        self.logout()
        self.assertNotLoggedIn()
        self.login()
        self.assertLoggedIn()

    def test_logout(self):
        self.assertLoggedIn()
        self.logout()
        self.assertNotLoggedIn()
