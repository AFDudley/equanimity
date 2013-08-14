DEBUG = True

SERVER_ADDRESS = '127.0.0.1'
SERVER_PORT = 5000
SERVER_NAME = SERVER_ADDRESS + ':' + str(SERVER_PORT)

CSRF_ENABLED = True
CSRF_SECRET_KEY = '\x08\x1d\x8e\x8e\xaeIy**0f\r\x11\x99\xe55b{m\x98\xc4-\xe1\x98\x16\xb1\xdcO\x15\x9e\xb4\x1a'

SECRET_KEY = '|/\xe2\x06\xbd\xc9D.\x08m\x95\x10\r\xd4\x1dN\xda\xa4\x01^`vYQ'
SESSION_COOKIE_DOMAIN = '127.0.0.1'
SESSION_COOKIE_HTTPONLY = True

BCRYPT_LOG_ROUNDS = 12

REMEMBER_COOKIE_DOMAIN = '127.0.0.1'

ZODB_STORAGE = 'file:///tmp/equanimity.fs'
