from formencode import Schema, Pipe, Invalid
from formencode.validators import (NotEmpty, Email, UnicodeString,
                                   FancyValidator)
from equanimity.player import Player, PASSWORD_LEN, EMAIL_LEN, USERNAME_LEN


class UniqueValidator(FancyValidator):

    available = None
    name = 'This'
    messages = dict(unavailable='%(name)s is not available.')

    def _validate_python(self, value, state):
        if not self.available(value):
            raise Invalid(self.message('unavailable', state, name=self.name),
                          value, state)


class UsernameExistsValidator(FancyValidator):
    messages = dict(not_found=u'Username %(username)s not found.')

    def _validate_python(self, value, state):
        state.user = Player.get_by_username(value)
        state.user_found = (state.user is not None)
        if state.user is None:
            raise Invalid(self.message('not_found', state, username=value),
                          value, state)


class PasswordValidator(FancyValidator):

    messages = dict(invalid='Invalid password.')

    def _validate_python(self, value, state):
        if (state.get('user_found', False) and
                not state.user.check_password(value)):
            raise Invalid(self.message('invalid', state), value, state)


class LoginForm(Schema):
    allow_extra_fields = True
    order = ['username', 'password']
    username = Pipe(NotEmpty(), UnicodeString(min=USERNAME_LEN['min'],
                                              max=USERNAME_LEN['max']),
                    UsernameExistsValidator())
    password = Pipe(NotEmpty(), UnicodeString(min=PASSWORD_LEN['min'],
                                              max=PASSWORD_LEN['max']),
                    PasswordValidator())


class SignupForm(Schema):
    allow_extra_fields = True
    username = Pipe(NotEmpty(), UnicodeString(min=USERNAME_LEN['min'],
                                              max=USERNAME_LEN['max']),
                    UniqueValidator(available=Player.username_available,
                                    name='Username'))
    email = Pipe(NotEmpty(), UnicodeString(max=EMAIL_LEN['max']),
                 Email(resolve_domain=False),
                 UniqueValidator(available=Player.email_available,
                                 name='Email'))
    password = Pipe(NotEmpty(), UnicodeString(min=PASSWORD_LEN['min'],
                                              max=PASSWORD_LEN['max']))
