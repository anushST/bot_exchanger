from src.exceptions import ClientError


class InvalidAddressError(ClientError):
    """Raises when address is invalid."""

    pass


class OutOFLimitisError(ClientError):
    """Raises when amount is out of limits."""

    pass


class PartnerInternalError(ClientError):
    """Raises when internal error oqqures."""

    pass


class IncorrectDirectionError(ClientError):
    """Raises when direction set incorrect."""

    pass


class NetworkError(ClientError):
    """Raises when ther is problems with a network."""

    pass


class TimeoutError(ClientError):
    """Rises when there is a timout of request."""

    pass


class DataProcessingError(ClientError):
    """Raises when there is an error with data processing."""

    pass


class MaximumRetriesError(ClientError):
    """Raises when maximum retries happen."""

    pass


class APIError(ClientError):
    """Raises when there is an error with api."""

    pass
