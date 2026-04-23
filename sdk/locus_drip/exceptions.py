class DripException(Exception):
    """Base exception for all Drip errors."""
    pass

class DripInsufficientCredits(DripException):
    """Raised when a user's credit balance is too low to proceed."""
    pass


class DripPlanLimitReached(DripException):
    """Raised when a user on a subscription plan hits their included unit cap."""
    pass


class DripPlanSwitchFailed(DripException):
    """Raised when an agent-driven plan switch cannot complete."""
    pass

class DripUserNotFound(DripException):
    """Raised when attempting to operate on an unregistered user."""
    pass
