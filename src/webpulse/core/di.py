"""Dependency injection container for the WebPulse auditing framework.

Manages instantiation and lifecycle of core service singletons.
"""

import threading
from typing import Any, cast

from webpulse.core.config import ConfigManager


class Container:
    """Centralized service locator and dependency injection container."""

    def __init__(self) -> None:
        """Initialize the dependency container."""
        self._lock = threading.Lock()
        self._services: dict[str, Any] = {}
        # Pre-populate built-in core service manager
        self.register("config_manager", ConfigManager())

    def register(self, name: str, service: Any) -> None:
        """Register a service singleton with the container.

        Args:
            name: String identifier of the service.
            service: Concrete instance to register.
        """
        with self._lock:
            self._services[name] = service

    def get(self, name: str) -> Any:
        """Retrieve a service instance from the container.

        Args:
            name: String identifier of the service.

        Returns:
            The registered service instance.

        Raises:
            KeyError: If the requested service is not registered.
        """
        with self._lock:
            if name not in self._services:
                raise KeyError(f"Service '{name}' is not registered in the container.")
            return self._services[name]

    @property
    def config_manager(self) -> ConfigManager:
        """Retrieve the registered ConfigManager instance."""
        return cast(ConfigManager, self.get("config_manager"))
