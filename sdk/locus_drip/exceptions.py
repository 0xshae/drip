class DripException(Exception):
    """Base exception for all Drip errors."""
    pass

class DripInsufficientCredits(DripException):
    """Raised when a user has insufficient credits for an operation."""
    pass

class DripUserNotFound(DripException):
    """Raised when attempting to operate on an unregistered user."""
    pass
