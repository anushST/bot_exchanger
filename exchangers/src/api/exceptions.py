from src.exceptions import ClientError

class InvalidAddressError(ClientError):
    """Raises when address is invalid."""
    pass

class OutOFLimitisError(ClientError):
    """Raises when amount is out of limits."""
    pass

class PartnerInternalError(ClientError):
    """Raises when internal error occurs."""
    pass

class IncorrectDirectionError(ClientError):
    """Raises when direction set incorrect."""
    pass

class NetworkError(ClientError):
    """Raises when there is problems with a network."""
    pass

class TimeoutError(ClientError):
    """Raises when there is a timeout of request."""
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

class RedisError(Exception):
    """Base exception for Redis errors."""
    pass

class RedisConnectionError(RedisError):
    """Exception for Redis connection errors."""
    pass

class RedisDataError(RedisError):
    """Exception for Redis data errors."""
    pass

class ApiError(Exception):
    """Base exception for API errors."""
    pass

class AuthenticationError(ApiError):
    """Exception for authentication errors."""
    pass

class ValidationApiError(ApiError):
    """Exception for API validation errors."""
    pass

class RateLimitError(ApiError):
    """Exception for rate limit errors."""
    pass

class InvalidPairError(ApiError):
    """Exception for invalid currency pair errors."""
    pass

class InvalidRateError(ApiError):
    """Exception for invalid exchange rate errors."""
    pass

class OrderCreationError(ApiError):
    """Exception for order creation errors."""
    pass

class DatabaseError(Exception):
    """Base exception for database-related errors."""
    pass

class TransactionNotFoundError(DatabaseError):
    """Raises when a transaction is not found in the database."""
    pass

class InvalidTransactionStatusError(ClientError):
    """Raises when a transaction has an invalid status."""
    pass

class CoinInfoNotFoundError(ApiError):
    """Raises when coin information is not found."""
    pass

class UnknownTransactionStatusError(ApiError):
    """Raises when an unknown transaction status is received from the API."""
    pass

class TransactionProcessingError(ClientError):
    """Raises when there is a general error during transaction processing."""
    pass