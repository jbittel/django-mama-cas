from django.contrib.auth.backends import ModelBackend
from django.contrib.auth.models import User


class ExceptionBackend(ModelBackend):
    """
    This authentication backend raises an exception on authentication
    for testing purposes.
    """
    def authenticate(self, username=None, password=None):
        raise Exception


class CaseInsensitiveBackend(ModelBackend):
    """
    A case-insenstitive authentication backend.
    """
    def authenticate(self, username=None, password=None):
        try:
            user = User.objects.get(username__iexact=username)
            if user.check_password(password):
                return user
        except User.DoesNotExist:
            return None
