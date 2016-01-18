class P2PException(Exception):
    pass


class P2PSlugTaken(P2PException):
    pass


class P2PNotFound(P2PException):
    pass


class P2PUniqueConstraintViolated(P2PException):
    pass


class P2PForbidden(P2PException):
    pass


class P2PEncodingMismatch(P2PException):
    pass


class P2PUnknownAttribute(P2PException):
    pass


class P2PInvalidAccessDefinition(P2PException):
    pass


class P2PSearchError(P2PException):
    pass
