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
            continue
    return False


def get_callbacks(service):
    for backend in _get_backends():
        callbacks = backend.get_callbacks(service)
        if callbacks:
            # TODO merge callback dicts?
            return callbacks
    return []


def get_logout_url(service):
    for backend in _get_backends():
        logout_url = backend.get_logout_url(service)
        if logout_url:
            return logout_url
    return None


def logout_allowed(service):
    return _is_allowed('logout_allowed', service)


def proxy_allowed(service):
    return _is_allowed('proxy_allowed', service)


def proxy_callback_allowed(service, pgturl):
    return _is_allowed('proxy_callback_allowed', service, pgturl)


def service_allowed(service):
    return _is_allowed('service_allowed', service)
