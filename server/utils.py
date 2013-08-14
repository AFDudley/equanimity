from urlparse import urlparse, urlunparse


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
