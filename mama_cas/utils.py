import urllib
import urlparse

from django.utils.http import urlquote


def add_query_params(url, params):
    for k in params.keys():
        if params[k] == '':
            del params[k]
    url_parts = list(urlparse.urlparse(url))
    query = dict(urlparse.parse_qs(url_parts[4]))
    query.update(params)
    url_parts[4] = urllib.urlencode(query)
    return urlparse.urlunparse(url_parts)

def url_encode(url):
    return urlquote(url, safe='')
