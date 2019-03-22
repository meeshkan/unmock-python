__all__ = ["UnmockException", "UnmockAuthorizationException", "UnmockServerUnavailableException"]

class UnmockException(Exception):
    pass

class UnmockAuthorizationException(UnmockException):
    pass

class UnmockServerUnavailableException(UnmockException):
    pass
