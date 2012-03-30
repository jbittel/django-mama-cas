import urllib
import urlparse

from django.utils.http import urlquote


def add_query_params(url, params):
    for k in params.keys():
        if params[k] == '':
            del params[k]

    parts = list(urlparse.urlparse(url))
    query = urlparse.parse_qs(parts[4])
    query.update(params)
    parts[4] = urllib.urlencode(query)
    return urlparse.urlunparse(parts)

#def clean_query(query, params):
#    for param in query.keys():
#        if param in params:
#            del query[param]
#    return query

def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip

def url_encode(url):
    if not url:
        return None
    return urlquote(url, safe='')
