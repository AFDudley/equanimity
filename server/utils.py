import time
import transaction
from threading import Lock
from urlparse import urlparse, urlunparse
from collections import Mapping
from server import db


def construct_full_url(url):
    # Convert a bare fqdn to full url with protocol
    parsed = urlparse(url)
    scheme = parsed.scheme
    netloc = parsed.netloc
    path = parsed.path
    if scheme not in ('http', 'https'):
        scheme = 'http'
    if not netloc:
        netloc = path.split('/')[0]
    if not path.startswith('/'):
        path = path.lstrip(netloc)
    if not path.endswith('/'):
        path += '/'
    parsed = parsed._replace(scheme=scheme, netloc=netloc, path=path)
    return urlunparse(parsed)


def api_error(err):
    """ Converts a error dict returned from a failed formencode Schema
    to something easier to work with """
    out = dict(main=[], fields={})
    if isinstance(err, basestring):
        out['main'].append(err)
    elif isinstance(err, Mapping):
        out['fields'].update(err)
    else:
        out['main'] += err
    return dict(errors=out)


class RateLimit(object):
    # http://flask.pocoo.org/snippets/70/
    expiration_window = 10

    lock = Lock()

    def __init__(self, key_prefix, limit, per):
        self.reset = (int(time.time()) // per) * per + per
        self.key = key_prefix + str(self.reset)
        self.limit = limit
        self.per = per
        with self.lock:
            self.current = db['rate_limit'][self.key].get_next_id()
            transaction.commit()

    remaining = property(lambda x: x.limit - x.current)
    over_limit = property(lambda x: x.current >= x.limit)
