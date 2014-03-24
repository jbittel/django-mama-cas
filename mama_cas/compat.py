from django.conf import settings


__all__ = ['user_model', 'get_username', 'SiteProfileNotAvailable', 'etree',
           'register_namespace']


# Django >= 1.5 uses AUTH_USER_MODEL to specify the currently active
# User model. Previous versions of Django do not have this setting
# and use the built-in User model.
#
# This is not needed when support for Django 1.4 is dropped.
user_model = getattr(settings, 'AUTH_USER_MODEL', 'auth.User')


# As custom user models can change the username field, Django >= 1.5
# uses get_username() to access the username field. Previous versions
# of Django do not have this method and access username directly.
#
# This is not needed when support for Django 1.4 is dropped.
def get_username(user):
    try:
        return user.get_username()
    except AttributeError:  # pragma: no cover
        return user.username


# The SiteProfileNotAvailable exception is raised from get_profile()
# when AUTH_PROFILE_MODULE is unavailable or invalid. With the
# arrival of custom User models in Django 1.5 this exception was
# deprecated, and removed entirely in Django 1.7.
#
# This is not needed when support for Django <= 1.6 is dropped.
try:
    from django.contrib.auth.models import SiteProfileNotAvailable
except ImportError:  # pragma: no cover
    class SiteProfileNotAvailable(Exception):
        pass


# Prefer cElementTree for performance, but fall back to the Python
# implementation in case C extentions are not available.
try:
    import xml.etree.cElementTree as etree
except ImportError:  # pragma: no cover
    import xml.etree.ElementTree as etree


# Provide access to the register_namespace() function. This function
# is not available in Python 2.6, and must be handled differently
# based on ElementTree or cElementTree being in use.
#
# This is not needed when support for Python 2.6 is dropped
try:
    register_namespace = etree.register_namespace
except AttributeError:  # pragma: no cover
    # ElementTree 1.2 (Python 2.6) does not have register_namespace()
    def register_namespace(prefix, uri):
        try:
            etree._namespace_map[uri] = prefix
        except AttributeError:
            # cElementTree 1.0.6 (Python 2.6) does not have
            # register_namespace() or _namespace_map, but
            # uses ElementTree for serialization
            import xml.etree.ElementTree as ET
            ET._namespace_map[uri] = prefix
