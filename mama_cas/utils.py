import urllib
import urlparse


def add_query_params(url, params):
    """
    Inject additional query parameters into an existing URL. If
    parameters already exist with the same name, they will be
    overwritten. Return the modified URL as a string.
    """
    # If any of the additional parameters have empty values,
    # ignore them
    params = dict([(k, v) for k, v in params.items() if v])

    parts = list(urlparse.urlparse(url))
    query = dict(urlparse.parse_qsl(parts[4]))
    query.update(params)
    parts[4] = urllib.urlencode(query)
    url = urlparse.urlunparse(parts)

    return url

def is_scheme_https(url):
    """
    Test the scheme of the parameter URL to see if it is HTTPS. If
    it is HTTPS return True, otherwise return False.
    """
    return 'https' == urlparse.urlparse(url).scheme
