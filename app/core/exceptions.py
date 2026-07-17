# Raised when a requested resource does not exist.
class NotFoundError(Exception):
    pass


# Raised when an operation conflicts with the current state of the data
# (e.g., creating a duplicate record or violating a business rule).
class ConflictError(Exception):
    pass

class PermissionDeniedError(Exception):
    """Raised when a user attempts to access a resource they do not own."""
    def __init__(self, message: str = "You do not have permission to access this resource."):
        self.message = message
class RateLimitExceededError(Exception):
    """Raised when a client exceeds the allowed number of requests."""
    def __init__(self, message: str = "Too many requests. Please try again later."):
        self.message = message