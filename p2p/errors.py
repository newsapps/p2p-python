class P2PException(Exception):
    pass


class P2PSlugTaken(P2PException):
    pass


class P2PNotFound(P2PException):
    pass


class P2PUniqueConstraintViolated(P2PException):
    pass


class P2PEncodingMismatch(P2PException):
    pass


class P2PUnknownAttribute(P2PException):
    pass


class P2PInvalidAccessDefinition(P2PException):
    pass


class P2PSearchError(P2PException):
    pass


class P2PRetryableError(P2PException):
    """
    A base exception for errors we want to retry when they fail.
    """
    pass


class P2PForbidden(P2PRetryableError):
    """
    To be raised when you credentials are refused due to a throttle.
    """
    pass


class P2PTimeoutError(P2PRetryableError):
    """
    To be raised when P2P throws a 500 error due to a timeout on its end.
    """
    pass
