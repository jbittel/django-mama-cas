from django.contrib.auth.backends import ModelBackend


class ExceptionBackend(ModelBackend):
    """
    This authentication backend raises an exception on authentication
    for testing purposes.
    """
    def authenticate(self, username=None, password=None):
        raise Exception
