# Raised when a requested resource does not exist.
class NotFoundError(Exception):
    pass


# Raised when an operation conflicts with the current state of the data
# (e.g., creating a duplicate record or violating a business rule).
class ConflictError(Exception):
    pass