"""Abstract Base Class and Metadata models for WebPulse plugins.

All analyzer modules (built-in and third-party) subclass BasePlugin.
"""

from abc import ABC, abstractmethod
from typing import Any

from pydantic import BaseModel, Field

from webpulse.reports.schemas import Finding, Target
from webpulse.utils.network import AsyncNetworkClient


class PluginMetadata(BaseModel):
    """Metadata schema representing plugin descriptor attributes."""

    name: str = Field(..., description="Unique slug name of the plugin.")
    category: str = Field(..., description="Plugin category (e.g. security, seo, performance).")
    version: str = Field(..., description="Plugin version (semantic version format).")


class BasePlugin(ABC):
    """Abstract base class that all WebPulse analyzer plugins must implement."""

    def __init__(self) -> None:
        """Initialize the plugin instances."""
        self.config: dict[str, Any] = {}

    @property
    @abstractmethod
    def metadata(self) -> PluginMetadata:
        """Retrieve plugin metadata descriptors."""
        pass

    async def on_load(self, config: dict[str, Any]) -> None:
        """Lifecycle hook executed during plugin initialization phase.

        Args:
            config: Key-value configuration parameters passed to the plugin.
        """
        self.config = config

    @abstractmethod
    async def execute(self, target: Target, client: AsyncNetworkClient) -> list[Finding]:
        """Run the core audit logic.

        Args:
            target: Target metadata.
            client: Secure network HTTPX connection client.

        Returns:
            List of findings generated during evaluation.
        """
        pass

    async def on_unload(self) -> None:  # noqa: B027
        """Lifecycle hook executed when destroying the plugin context."""
        pass


class_names = ["PluginMetadata", "BasePlugin"]
