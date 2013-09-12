import time
from urlparse import urlparse, urlunparse
from collections import Mapping
from server import redis


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


class AttributeDict(dict):
    """ Object that allows .attr access to a dictionary """
    def __setattr__(self, k, v):
        return dict.__setitem__(self, k, v)

    def __getattribute__(self, key):
        if key in self:
            return dict.__getitem__(self, key)
        return object.__getattribute__(self, key)


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

    def __init__(self, key_prefix, limit, per):
        self.reset = (int(time.time()) // per) * per + per
        self.key = key_prefix + str(self.reset)
        self.limit = limit
        self.per = per
        p = redis.pipeline()
        p.incr(self.key)
        p.expireat(self.key, self.reset + self.expiration_window)
        self.current = min(p.execute()[0], limit)

    remaining = property(lambda x: x.limit - x.current)
    over_limit = property(lambda x: x.current >= x.limit)
