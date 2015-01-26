from django.conf import settings


# Django >= 1.5 uses AUTH_USER_MODEL to specify the currently active
# User model. Previous versions of Django do not have this setting
# and use the built-in User model.
#
# This is not needed when support for Django 1.4 is dropped.
user_model = getattr(settings, 'AUTH_USER_MODEL', 'auth.User')


# In Django >= 1.5 get_user_model() returns the currently active
# User model. Previous versions of Django have no concept of custom
# User models and reference User directly.
#
# This is not needed when support for Django 1.4 is dropped.
try:
    from django.contrib.auth import get_user_model
except ImportError:  # pragma: no cover
    from django.contrib.auth.models import User
    get_user_model = lambda: User


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


# Prefer cElementTree for performance, but fall back to the Python
# implementation in case C extensions are not available.
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


# gevent is optional, and allows for asynchronous single sign-out
# requests. If it is not present, synchronous requests will be sent.
try:
    import gevent
except ImportError:  # pragma: no cover
    gevent = None


# defusedxml is optional, and is used for the /samlValidate
# endpoint. If it is not present, this endpoint raises an exception.
try:
    import defusedxml.ElementTree as defused_etree
except ImportError:  # pragma: no cover
    defused_etree = None


# Support both Python 2 and Python 3 locations for urllib imports.
try:
    from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse
except ImportError:  # pragma: no cover
    from urllib import urlencode
    from urlparse import parse_qsl, urlparse, urlunparse
