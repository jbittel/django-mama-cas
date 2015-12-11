import logging
import re

from django.conf import settings
from django.core.exceptions import PermissionDenied
from django.core import urlresolvers
from django.http import HttpResponseRedirect
from django.utils.encoding import force_bytes

from .compat import parse_qsl
from .compat import urlencode
from .compat import urlparse
from .compat import urlunparse


logger = logging.getLogger(__name__)


def add_query_params(url, params):
    """
    Inject additional query parameters into an existing URL. If
    parameters already exist with the same name, they will be
    overwritten. Parameters with empty values are ignored. Return
    the modified URL as a string.
    """
    encode = lambda v: force_bytes(v, settings.DEFAULT_CHARSET)
    params = dict([(encode(k), encode(v)) for k, v in params.items() if v])

    parts = list(urlparse(url))
    query = dict(parse_qsl(parts[4]))
    query.update(params)
    parts[4] = urlencode(query)
    return urlunparse(parts)


def is_scheme_https(url):
    """
    Test the scheme of the parameter URL to see if it is HTTPS. If
    it is HTTPS return ``True``, otherwise return ``False``.
    """
    return 'https' == urlparse(url).scheme


def clean_service_url(url):
    """
    Return only the scheme, hostname (with optional port) and path
    components of the parameter URL.
    """
    parts = urlparse(url)
    return urlunparse((parts.scheme, parts.netloc, parts.path, '', '', ''))


def match_service(service1, service2):
    """
    Compare two service URLs. Return ``True`` if the scheme, hostname,
    optional port and path match.
    """
    s1, s2 = urlparse(service1), urlparse(service2)
    try:
        return (s1.scheme, s1.netloc, s1.path) == (s2.scheme, s2.netloc, s2.path)
    except ValueError:
        return False


def is_valid_service_url(url):
    """
    Check the provided URL against the configured list of valid service
    URLs. If the service URL matches at least one valid service, return
    ``True``, otherwise return ``False``. If no valid service URLs are
    configured, return ``True``.
    """
    valid_services = getattr(settings, 'MAMA_CAS_VALID_SERVICES', ())
    if not valid_services:
        return True
    for service in [re.compile(s) for s in valid_services]:
        if service.match(url):
            return True
    return False


def redirect(to, *args, **kwargs):
    """
    Similar to the Django ``redirect`` shortcut but with altered
    functionality. If an optional ``params`` argument is provided, the
    dictionary items will be injected as query parameters on the
    redirection URL.
    """
    params = kwargs.pop('params', {})

    try:
        to = urlresolvers.reverse(to, args=args, kwargs=kwargs)
    except urlresolvers.NoReverseMatch:
        if '/' not in to and '.' not in to:
            to = urlresolvers.reverse('cas_login')
        elif not is_valid_service_url(to):
            raise PermissionDenied()

    if params:
        to = add_query_params(to, params)

    logger.debug("Redirecting to %s" % to)
    return HttpResponseRedirect(to)


def to_bool(str):
    """
    Converts a given string to a boolean value. Leading and trailing
    whitespace is ignored, so strings of whitespace are evaluated as
    ``False``.
    """
    if str:
        return bool(str.strip())
    return False
