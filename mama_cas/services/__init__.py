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


def get_callbacks(service):
    callbacks = []
    for backend in _get_backends():
        try:
            callbacks = callbacks + backend.get_callbacks(service)
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
    return _is_allowed('logout_allowed', service)


def proxy_allowed(service):
    return _is_allowed('proxy_allowed', service)


def proxy_callback_allowed(service, pgturl):
    return _is_allowed('proxy_callback_allowed', service, pgturl)


def service_allowed(service):
    return _is_allowed('service_allowed', service)
