# Raised when a requested resource does not exist.
class NotFoundError(Exception):
    pass


# Raised when an operation conflicts with the current state of the data
# (e.g., creating a duplicate record or violating a business rule).
class ConflictError(Exception):
    pass


class BusinessRuleViolation(Exception):
    """Raised when a core domain business rule is violated (e.g. moving a qualified lead back to new)."""
    def __init__(self, message: str = "Business rule violation"):
        self.message = message
        super().__init__(self.message)


class PermissionDeniedError(Exception):
    """Raised when a user attempts to access a resource they do not own."""
    def __init__(self, message: str = "You do not have permission to access this resource."):
        self.message = message
        super().__init__(self.message)


class RateLimitExceededError(Exception):
    """Raised when a client exceeds the allowed number of requests."""
    def __init__(self, message: str = "Too many requests. Please try again later."):
        self.message = message
        super().__init__(self.message)


class AuthenticationError(Exception):
    """Maps to HTTP 401 Unauthorized"""
    def __init__(self, message: str = "Incorrect email or password."):
        super().__init__(message)


class UserAlreadyExistsError(ConflictError):
    """Maps to HTTP 409 Conflict"""
    def __init__(self, email: str):
        super().__init__(f"A user with email '{email}' already exists.")