"""Custom exception classes for the WebPulse auditing framework.

All exceptions in the WebPulse framework inherit from the base class WebPulseException
to support structured error handling and prevent leakage of raw tracebacks.
"""


class WebPulseException(Exception):
    """Base exception class for all errors in the WebPulse framework."""

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message

    def __str__(self) -> str:
        return f"{self.__class__.__name__}: {self.message}"


class ConfigurationException(WebPulseException):
    """Raised when configuration validation, file parsing, or type binding fails."""

    def __init__(self, message: str) -> None:
        super().__init__(message)


class SecurityException(WebPulseException):
    """Raised when a security boundary is violated.

    For example, SSRF block or unauthorized plugin imports.
    """

    def __init__(self, message: str) -> None:
        super().__init__(message)


class PluginException(WebPulseException):
    """Raised when plugin loading, manifest validation, or runtime lifecycle execution fails."""

    def __init__(self, message: str) -> None:
        super().__init__(message)
