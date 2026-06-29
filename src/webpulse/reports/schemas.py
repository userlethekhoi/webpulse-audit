"""Data schemas for WebPulse reports and findings.

Defines Pydantic models for Target objects, Severity levels, Evidence items, and Finding items.
"""

import hashlib
from enum import StrEnum
from typing import Any, Literal

from pydantic import BaseModel, Field, model_validator


class Target(BaseModel):
    """Scan target representation."""

    url: str = Field(..., description="Target website URL.")
    ip_address: str | None = Field(default=None, description="Resolved IP address of the target.")


class Severity(StrEnum):
    """Severity levels for audit findings."""

    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    INFO = "INFO"


class Evidence(BaseModel):
    """Evidence supporting a finding."""

    type: Literal["http_header", "html_snippet", "time_ms", "cert_property"] = Field(
        ..., description="Type of evidence parsed."
    )
    data: str = Field(..., description="Raw evidence details.")


class Finding(BaseModel):
    """An individual security, SEO, performance, or accessibility issue discovered."""

    id: str = Field(default="", description="Deterministic SHA-256 identification hash.")
    plugin_name: str = Field(..., description="Name of the plugin that raised this finding.")
    category: str = Field(..., description="Audit category (e.g. security, seo).")
    target_url: str = Field(..., description="The URL audited.")
    title: str = Field(..., description="Title of the issue.")
    severity: Severity = Field(..., description="Impact severity classification.")
    confidence: float = Field(default=1.0, ge=0.0, le=1.0, description="Audit confidence level.")
    description: str = Field(..., description="Detailed description of the issue.")
    remediation: str = Field(..., description="Specific repair instructions.")
    evidence: list[Evidence] = Field(default_factory=list, description="Evidence list.")

    @model_validator(mode="before")
    @classmethod
    def populate_id(cls, data: Any) -> Any:
        """Automatically compute a deterministic SHA-256 ID if none is provided."""
        if isinstance(data, dict):
            tid = data.get("id")
            if not tid:
                target_url = data.get("target_url", "")
                plugin_name = data.get("plugin_name", "")
                title = data.get("title", "")
                hash_input = f"{target_url}:{plugin_name}:{title}"
                data["id"] = hashlib.sha256(hash_input.encode("utf-8")).hexdigest()
        return data
