DEBUG = True
TESTING = True
DEBUG_LOGGING = True

SERVER_NAME = 'aequal.is'
#SERVER_NAME = '127.0.0.1:5000'

SEASURF_INCLUDE_OR_EXEMPT_VIEWS = 'include'
CSRF_DISABLED = True
CSRF_SECRET_KEY = u'\x06?\xc3moBQE\xd6\xb3\x96\xc5Q9^\xd8\xcf\x90\xc4-\xa2\xd5\xd1\x1f\xd4\x82\xa8a|\x01-\x18'

SECRET_KEY = u'\xbf\x81\x95\xe8\xfa\xd2\xc3\xb0\xc8\x89\xd6\xffk\x08:\xaby\xef\x8dT\x11CE\x13\xf3\xder\xfd\xc7_\ty'
SESSION_COOKIE_DOMAIN = SERVER_NAME.split(':')[0]
SESSION_COOKIE_HTTPONLY = True

BCRYPT_LOG_ROUNDS = 12

REMEMBER_COOKIE_DOMAIN = SESSION_COOKIE_DOMAIN

ZODB_STORAGE = 'zeo://localhost:9100'
