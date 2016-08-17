import re
import warnings

from django.conf import settings
from django.utils.module_loading import import_string


def _get_backends():
    backends = []
    for backend_path in ['mama_cas.services.backends.SettingsBackend']:
        backend = import_string(backend_path)()
        backends.append(backend)
    return backends


def _is_allowed(attr, *args):
    for backend in _get_backends():
        try:
            if getattr(backend, attr)(*args):
                return True
        except AttributeError:
            raise NotImplementedError("%s does not implement %s()" % (backend, attr))
    return False


def _is_valid_service_url(url):
    valid_services = getattr(settings, 'MAMA_CAS_VALID_SERVICES', ())
    if not valid_services:
        return True
    warnings.warn(
        'The MAMA_CAS_VALID_SERVICES setting is deprecated. Services '
        'should be configured using MAMA_CAS_SERVICES.', DeprecationWarning)
    for service in [re.compile(s) for s in valid_services]:
        if service.match(url):
            return True
    return False


def get_callbacks(service):
    callbacks = list(getattr(settings, 'MAMA_CAS_ATTRIBUTE_CALLBACKS', []))
    if callbacks:
        warnings.warn(
            'The MAMA_CAS_ATTRIBUTE_CALLBACKS setting is deprecated. Service callbacks '
            'should be configured using MAMA_CAS_SERVICES.', DeprecationWarning)

    for backend in _get_backends():
        try:
            callbacks.extend(backend.get_callbacks(service))
        except AttributeError:
            raise NotImplementedError("%s does not implement get_callbacks()" % backend)
    return callbacks


def get_logout_url(service):
    for backend in _get_backends():
        try:
            return backend.get_logout_url(service)
        except AttributeError:
            raise NotImplementedError("%s does not implement get_logout_url()" % backend)
    return None


def logout_allowed(service):
    if getattr(settings, 'MAMA_CAS_SERVICES', {}):
        return _is_allowed('logout_allowed', service)

    if getattr(settings, 'MAMA_CAS_ENABLE_SINGLE_SIGN_OUT', False):
        warnings.warn(
            'The MAMA_CAS_ENABLE_SINGLE_SIGN_OUT setting is deprecated. SLO '
            'should be configured using MAMA_CAS_SERVICES.', DeprecationWarning)
        return True


def proxy_allowed(service):
    return _is_allowed('proxy_allowed', service)


def proxy_callback_allowed(service, pgturl):
    if getattr(settings, 'MAMA_CAS_SERVICES', {}):
        return _is_allowed('proxy_callback_allowed', service, pgturl)
    return _is_valid_service_url(service)


def service_allowed(service):
    if getattr(settings, 'MAMA_CAS_SERVICES', {}):
        return _is_allowed('service_allowed', service)
    return _is_valid_service_url(service)
