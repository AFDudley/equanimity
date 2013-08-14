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

