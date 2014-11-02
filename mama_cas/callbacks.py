from .compat import get_username


def user_name_attributes(user, service):
    """Return all available user name related fields and methods."""
    attributes = {}
    attributes['username'] = get_username(user)
    attributes['full_name'] = user.get_full_name()
    try:
        attributes['short_name'] = user.get_short_name()
    except AttributeError:  # pragma: no cover
        # Django 1.4 does not provide this method
        pass
    return attributes


def user_model_attributes(user, service):
    """
    Return all fields on the user object that are not in the list
    of fields to ignore.
    """
    ignore_fields = ['id', 'password']
    attributes = {}
    for field in user._meta.fields:
        if field.name not in ignore_fields:
            attributes[field.name] = getattr(user, field.name)
    return attributes
