class DatabaseError(Exception):
    """Raises when there are database error."""

    pass


class RedisError(Exception):
    """Raises when there are error with redis."""

    pass


class ClientError(Exception):
    """The base class for client errors."""

    pass
