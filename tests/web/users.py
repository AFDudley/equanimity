from ..base import FlaskTestDB


class UserTestBase(FlaskTestDB):

    def setUp(self):
        super(UserTestBase, self).setUp()
        self.email = 'teST@gmail.com'
        self.username = 'testuserX'
        self.password = 'testtest'
        self.uid = 1

    @property
    def user_schema(self):
        return dict(username=self.username, email=self.email.lower(),
                    uid=self.uid)

    def get_create_user_data(self):
        return dict(username=self.username, password=self.password,
                    email=self.email)

    def get_login_user_data(self):
        data = self.get_create_user_data()
        del data['email']
        return data

    def create_user(self, data=None):
        if data is None:
            data = self.get_create_user_data()
        r = self.post('users.signup', data=data)
        self.assert200(r)
        return r

    def get_user(self):
        return self.db['players'][self.uid]

    def logout(self):
        r = self.get('users.logout')
        self.assert200(r)
        return r

    def login(self, check_status=True, **kwargs):
        r = self.post('users.login', data=self.get_login_user_data(), **kwargs)
        if check_status:
            self.assert200(r)
        return r

    def assertUserExists(self):
        users = [self.db['player_username'][self.username.lower()],
                 self.db['player_email'][self.email.lower()],
                 self.db['players'][self.uid]]
        for user in users:
            self.assertEqual(user.uid, 1)
            self.assertEqual(user.username, self.username.lower())
            self.assertEqual(user.display_username, self.username)
            self.assertEqual(user.email, self.email.lower())
            self.assertTrue(user.password)

    def assertUserNotExists(self):
        self.assertEqual(self.db['player_uid'].uid, 0)

    def assertLoggedIn(self, r=None):
        if r is None:
            r = self.get('users.me')
        self.assertValidJSON(r, self.user_schema)
        self.assert200(r)

    def assertNotLoggedIn(self):
        r = self.get('frontend.index')
        self.assert200(r)
        self.assertNotIn(self.username, r.data)
        self.assertNotIn('Logout', r.data)
        self.assertIn('Login', r.data)
        self.assertIn('Signup', r.data)

    def assertUserCount(self, ct):
        self.assertEqual(self.db['player_uid'].uid, ct)


class SignupTest(UserTestBase):

    def test_signup(self):
        self.create_user()
        self.assertUserExists()
        self.assertLoggedIn()
        self.assertUserCount(1)

    def test_signup_username_in_use(self):
        self.test_signup()
        self.logout()
        # same username (uppercased to test case-insensitivity)
        self.username = self.username.upper()
        # different email
        self.email = 'tecmascWADmsad@yahoo.com'
        self.create_user()
        self.assertNotLoggedIn()
        self.assertUserCount(1)

    def test_signup_email_in_use(self):
        self.test_signup()
        self.logout()
        # change username
        self.username *= 2
        # but use same email (uppercased to test case-insensitivity)
        self.email = self.email.upper()
        self.create_user()
        self.assertNotLoggedIn()
        self.assertUserCount(1)

    def test_bad_username(self):
        data = self.get_create_user_data()
        data['username'] = 'x' * 1024
        self.create_user(data=data)
        self.assertUserNotExists()

    def test_missing_username(self):
        data = self.get_create_user_data()
        del data['username']
        self.create_user(data=data)
        self.assertUserNotExists()

    def test_bad_password(self):
        data = self.get_create_user_data()
        data['password'] = 'xxx'
        self.create_user(data=data)
        self.assertUserNotExists()

    def test_missing_password(self):
        data = self.get_create_user_data()
        del data['password']
        self.create_user(data=data)
        self.assertUserNotExists()

    def test_bad_email(self):
        data = self.get_create_user_data()
        data['email'] = 'gmail.com'
        self.create_user(data=data)
        self.assertUserNotExists()

    def test_missing_email(self):
        data = self.get_create_user_data()
        del data['email']
        self.create_user(data=data)
        self.assertUserNotExists()


class LoginTest(UserTestBase):

    def setUp(self):
        super(LoginTest, self).setUp()
        self.create_user()
        self.logout()

    def test_login(self):
        self.assertNotLoggedIn()
        self.assertUserExists()
        self.login()
        self.assertLoggedIn()

    def test_login_wrong_password(self):
        self.assertNotLoggedIn()
        self.assertUserExists()
        self.password *= 2
        self.login()
        self.assertNotLoggedIn()

    def test_login_unknown_username(self):
        self.assertNotLoggedIn()
        self.assertUserExists()
        self.username *= 2
        self.login()
        self.assertNotLoggedIn()

    def test_already_logged_in(self):
        self.assertNotLoggedIn()
        self.assertUserExists()
        self.login()
        self.assertLoggedIn()
        r = self.login()
        self.assertLoggedIn(r)

    def test_logout(self):
        self.login()
        self.assertLoggedIn()
        self.logout()
        self.assertNotLoggedIn()
