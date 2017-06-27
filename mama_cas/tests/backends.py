from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend

from mama_cas.services.backends import SettingsBackend


class ExceptionBackend(ModelBackend):
    """Raise an exception on authentication for testing purposes."""
    def authenticate(self, request, username=None, password=None):
        raise Exception


class CaseInsensitiveBackend(ModelBackend):
    """A case-insenstitive authentication backend."""
    def authenticate(self, request, username=None, password=None):
        user_model = get_user_model()
        try:
            user = user_model.objects.get(username__iexact=username)
            if user.check_password(password):
                return user
        except user_model.DoesNotExist:
            return None


class CustomTestServiceBackend(SettingsBackend):
    """Service backend that always allows any service containing 'test.com'"""
    def service_allowed(self, service):
        if service and "test.com" in service:
            return True
        return super(CustomTestServiceBackend, self).service_allowed(service)


class CustomTestInvalidServiceBackend(object):
    pass
