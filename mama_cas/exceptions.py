"""
A set of custom exceptions corresponding to the minimum set of
error codes that all CAS servers must implement.
"""


class Error(Exception):
    """
    Base class for all custom exception types.
    """
    def __str__(self):
        return self.msg


class InvalidRequestError(Error):
    """
    Not all of the required parameters are present.
    """
    def __init__(self, msg):
        self.code = 'INVALID_REQUEST'
        self.msg = msg


class InvalidTicketError(Error):
    """
    The ticket provided is not valid, or the ticket was not issued
    from primary credentials and renew is present.
    """
    def __init__(self, msg):
        self.code = 'INVALID_TICKET'
        self.msg = msg


class InvalidServiceError(Error):
    """
    The service specified does not match the service identifier
    associated with the ticket.
    """
    def __init__(self, msg):
        self.code = 'INVALID_SERVICE'
        self.msg = msg


class InternalError(Error):
    """
    An internal error occurred during ticket validation.
    """
    def __init__(self, msg):
        self.code = 'INTERNAL_ERROR'
        self.msg = msg


class BadPGTError(Error):
    """
    The PGT provided was invalid
    """
    def __init__(self, msg):
        self.code = 'BAD_PGT'
        self.msg = msg
