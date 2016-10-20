from mama_cas.exceptions import InternalError


def raise_exception(user, service):
    """Raise an exception for testing purposes."""
    raise InternalError('Error in attribute callback')
