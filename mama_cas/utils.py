import logging
import re
import warnings

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.core.exceptions import PermissionDenied
from django.core import urlresolvers
from django.http import HttpResponseRedirect
from django.utils import six
from django.utils.encoding import force_bytes
from django.utils.functional import cached_property

from .compat import parse_qsl
from .compat import urlencode
from .compat import urlparse
from .compat import urlunparse


logger = logging.getLogger(__name__)


class ServiceConfig(object):
    PROXY_ALLOW_DEFAULT = False
    CALLBACKS_DEFAULT = []
    LOGOUT_ALLOW_DEFAULT = False
    LOGOUT_URL_DEFAULT = None

    @cached_property
    def services(self):
        services = []

        for service in getattr(settings, 'MAMA_CAS_VALID_SERVICES', []):
            if isinstance(service, six.string_types):
                warnings.warn(
                    'Service URL configuration is changing. Check the documentation '
                    'for the MAMA_CAS_VALID_SERVICES setting.', DeprecationWarning)
                match = re.compile(service)
                service = {'SERVICE': service}
            else:
                service = service.copy()
                try:
                    match = re.compile(service['SERVICE'])
                except KeyError:
                    raise ImproperlyConfigured(
                        'Missing SERVICE key for service configuration. '
                        'Check your MAMA_CAS_VALID_SERVICES setting.')

            service['MATCH'] = match
            # TODO For transitional backwards compatibility, this defaults to True.
            service.setdefault('PROXY_ALLOW', True)
            service.setdefault('CALLBACKS', self.CALLBACKS_DEFAULT)
            service.setdefault('LOGOUT_ALLOW', self.LOGOUT_ALLOW_DEFAULT)
            service.setdefault('LOGOUT_URL', self.LOGOUT_URL_DEFAULT)
            try:
                service['PROXY_PATTERN'] = re.compile(service['PROXY_PATTERN'])
            except KeyError:
                pass
            services.append(service)

        return services

    def get_service(self, s):
        for service in self.services:
            if service['MATCH'].match(s):
                return service
        return {}

    def is_valid(self, s):
        if not self.services:
            return True
        return bool(self.get_service(s))


services = ServiceConfig()


def get_config(service, setting):
    """Access the configuration for a given service and setting."""
    try:
        return services.get_service(service)[setting]
    except KeyError:
        return getattr(services, setting + '_DEFAULT')


def add_query_params(url, params):
    """
    Inject additional query parameters into an existing URL. If
    parameters already exist with the same name, they will be
    overwritten. Parameters with empty values are ignored. Return
    the modified URL as a string.
    """
    def encode(s):
        return force_bytes(s, settings.DEFAULT_CHARSET)
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


def is_valid_service(service):
    """
    Check the provided service against the configured list of valid
    services.
    """
    if not service:
        return False
    return services.is_valid(service)


def is_valid_proxy_callback(service, pgturl):
    """
    Check the provided proxy callback against the configured allowable
    callback pattern. If no pattern is configured, return `True`.
    """
    try:
        return get_config(service, 'PROXY_PATTERN').match(pgturl)
    except AttributeError:
        # TODO For transitional backwards compatibility, check against valid services
        if is_valid_service(pgturl):
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
        elif not is_valid_service(to):
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
