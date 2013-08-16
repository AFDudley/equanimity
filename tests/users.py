import transaction
from base import FlaskTestDB


class UserTestBase(FlaskTestDB):

    def setUp(self):
        super(UserTestBase, self).setUp()
        self.email = 'teST@gmail.com'
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

    def create_user(self, data=None):
        if data is None:
            data = self.get_create_user_data()
        r = self.post('users.signup', data=data)
        self.assert200(r)
        return r

    def get_user(self):
        return self.db['player'][self.uid]

    def logout(self):
        r = self.get('users.logout')
        self.assert200(r)
        return r

    def login(self, check_status=True):
        r = self.post('users.login', data=self.get_login_user_data())
        if check_status:
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
            self.assertEqual(user.email, self.email.lower())
            self.assertTrue(user.password)

    def assertUserNotExists(self):
        self.assertEqual(self.db['player_uid'].uid, 0)

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
        r = self.create_user(data=data)
        self.assertUserNotExists()

    def test_missing_username(self):
        data = self.get_create_user_data()
        del data['username']
        r = self.create_user(data=data)
        self.assertUserNotExists()

    def test_bad_password(self):
        data = self.get_create_user_data()
        data['password'] = 'xxx'
        r = self.create_user(data=data)
        self.assertUserNotExists()

    def test_missing_password(self):
        data = self.get_create_user_data()
        del data['password']
        r = self.create_user(data=data)
        self.assertUserNotExists()

    def test_bad_email(self):
        data = self.get_create_user_data()
        data['email'] = 'gmail.com'
        r = self.create_user(data=data)
        self.assertUserNotExists()

    def test_missing_email(self):
        data = self.get_create_user_data()
        del data['email']
        r = self.create_user(data=data)
        self.assertUserNotExists()

    def test_signup_page(self):
        r = self.get('users.signup')
        self.assert200(r)


class LoginTest(UserTestBase):

    def setUp(self):
        super(LoginTest, self).setUp()
        self.create_user()
        self.logout()

    def test_login_page(self):
        r = self.get('users.login')
        self.assert200(r)

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
        self.assertIn('Currently logged in', r.data)
        self.assertLoggedIn()

    def test_login_suspended(self):
        self.assertNotLoggedIn()
        self.assertUserExists()
        user = self.get_user()
        user.suspended = True
        transaction.commit()
        r = self.login(check_status=False)
        self.assert500(r)
        self.assertNotLoggedIn()

    def test_logout(self):
        self.login()
        self.assertLoggedIn()
        self.logout()
        self.assertNotLoggedIn()
