"""Configuration module for the WebPulse auditing framework.

Exposes Pydantic settings models for core, network, crawler, authentication,
module-specific, and reporting parameters, and resolves overrides based on priority hierarchy.
"""

import copy
import json
import os
import re
from pathlib import Path
from typing import Any, Literal

import yaml
from pydantic import BaseModel, Field, ValidationError

from webpulse.core.exceptions import ConfigurationException

# Predefined scan profiles
PROFILES: dict[str, dict[str, Any]] = {
    "fast": {
        "core": {"rate_limit": 50, "max_connections": 100},
        "modules": {
            "security": {"enabled": True, "sqli_check": False},
            "seo": {"enabled": False},
            "waf": {"enabled": True},
            "performance": {"enabled": True, "use_browser": False},
            "accessibility": {"enabled": False},
            "http": {"enabled": True},
            "ssl": {"enabled": True},
        },
    },
    "default": {
        "core": {"rate_limit": 15, "max_connections": 30},
        "modules": {
            "security": {"enabled": True, "sqli_check": True},
            "seo": {"enabled": True},
            "waf": {"enabled": True},
            "performance": {"enabled": True, "use_browser": False},
            "accessibility": {"enabled": True},
            "http": {"enabled": True},
            "ssl": {"enabled": True},
        },
    },
    "full": {
        "core": {"rate_limit": 10, "max_connections": 10},
        "modules": {
            "security": {"enabled": True, "sqli_check": True},
            "seo": {"enabled": True},
            "waf": {"enabled": True},
            "performance": {"enabled": True, "use_browser": True},
            "accessibility": {"enabled": True},
            "http": {"enabled": True},
            "ssl": {"enabled": True},
        },
    },
}


class CoreConfig(BaseModel):
    """Core settings configuration parameters."""

    rate_limit: int = Field(default=15, ge=1, le=200)
    max_connections: int = Field(default=30, ge=1)
    timeout: int = Field(default=12, ge=1)
    sandbox_plugins: bool = Field(default=True)
    fail_on_health: int = Field(default=80, ge=0, le=100)
    fail_on_critical: bool = Field(default=True)


class NetworkConfig(BaseModel):
    """Outbound socket and connection settings."""

    allow_private_ips: bool = Field(default=False)
    user_agent: str = Field(default="WebPulse-Audit-Agent/2.0 (Defensive Website Audit Tool)")


class CrawlerConfig(BaseModel):
    """BFS crawling settings."""

    enabled: bool = Field(default=True)
    max_depth: int = Field(default=2, ge=0)
    max_pages: int = Field(default=15, ge=1)
    follow_subdomains: bool = Field(default=False)
    exclude_patterns: list[str] = Field(default_factory=lambda: [r"\.pdf$", r"\.zip$", r"/logout"])


class AuthConfig(BaseModel):
    """Authentication and session state configurations."""

    enabled: bool = Field(default=False)
    login_url: str | None = Field(default=None)
    method: str = Field(default="post_json")
    credentials: dict[str, str] = Field(default_factory=dict)
    token_injection: dict[str, str] = Field(default_factory=dict)


class SecurityModuleConfig(BaseModel):
    """Security headers scanner settings."""

    enabled: bool = Field(default=True)
    check_paths: list[str] = Field(default_factory=lambda: ["/.git/config", "/.env"])
    require_headers: list[str] = Field(
        default_factory=lambda: ["Content-Security-Policy", "Strict-Transport-Security"]
    )
    sqli_check: bool = Field(default=True)
    sqli_timeout: int = Field(default=8, ge=1, le=30)


class SeoModuleConfig(BaseModel):
    """SEO analyzer settings."""

    enabled: bool = Field(default=True)
    check_meta_description: bool = Field(default=True)


class WafModuleConfig(BaseModel):
    """WAF detector settings."""

    enabled: bool = Field(default=True)
    confidence_threshold: int = Field(default=40, ge=0, le=100)


class PerformanceModuleConfig(BaseModel):
    """Performance analyzer settings."""

    enabled: bool = Field(default=True)
    use_browser: bool = Field(default=False)
    connection_timeout_ms: int = Field(default=5000, ge=0)


class AccessibilityModuleConfig(BaseModel):
    """Accessibility analyzer settings."""

    enabled: bool = Field(default=True)


class HttpModuleConfig(BaseModel):
    """HTTP analyzer settings."""

    enabled: bool = Field(default=True)


class SslModuleConfig(BaseModel):
    """SSL analyzer settings."""

    enabled: bool = Field(default=True)
    verify_expiry_days: int = Field(default=14, ge=1)


class ModulesConfig(BaseModel):
    """Toggles and settings for individual audit modules."""

    security: SecurityModuleConfig = Field(default_factory=SecurityModuleConfig)
    seo: SeoModuleConfig = Field(default_factory=SeoModuleConfig)
    waf: WafModuleConfig = Field(default_factory=WafModuleConfig)
    performance: PerformanceModuleConfig = Field(default_factory=PerformanceModuleConfig)
    accessibility: AccessibilityModuleConfig = Field(default_factory=AccessibilityModuleConfig)
    http: HttpModuleConfig = Field(default_factory=HttpModuleConfig)
    ssl: SslModuleConfig = Field(default_factory=SslModuleConfig)


class ReportingConfig(BaseModel):
    """Report outputs and directories settings."""

    formats: list[str] = Field(default_factory=lambda: ["console", "json"])
    output_dir: str = Field(default="./webpulse-reports")
    report_name_template: str = Field(default="webpulse-report-{target}-{timestamp}")


class AppConfig(BaseModel):
    """WebPulse main configuration model."""

    core: CoreConfig = Field(default_factory=CoreConfig)
    network: NetworkConfig = Field(default_factory=NetworkConfig)
    crawler: CrawlerConfig = Field(default_factory=CrawlerConfig)
    auth: AuthConfig = Field(default_factory=AuthConfig)
    modules: ModulesConfig = Field(default_factory=ModulesConfig)
    reporting: ReportingConfig = Field(default_factory=ReportingConfig)
    profile: Literal["fast", "default", "full"] = Field(default="default")


class ConfigManager:
    """Loads, merges, and validates WebPulse configurations."""

    def __init__(self) -> None:
        """Initialize the ConfigManager."""
        self._current_config: AppConfig | None = None

    def load_config(self, filepath: Path | None = None) -> AppConfig:
        """Load configuration from a file, merge env variables, and validate schemas.

        Args:
            filepath: Path to the target YAML, JSON, or TOML file.

        Returns:
            The resolved and validated AppConfig instance.

        Raises:
            ConfigurationException: If parsing fails or variables violate type rules.
        """
        config_dict: dict[str, Any] = {}

        # Resolve config file path if not provided
        target_file = filepath
        if not target_file:
            # Check default locations
            cwd_yaml = Path.cwd() / "webpulse.yaml"
            cwd_yml = Path.cwd() / "webpulse.yml"
            user_config = Path.home() / ".webpulse" / "config.yaml"

            if cwd_yaml.exists():
                target_file = cwd_yaml
            elif cwd_yml.exists():
                target_file = cwd_yml
            elif user_config.exists():
                target_file = user_config

        # Parse configuration file
        if target_file and target_file.exists():
            try:
                with open(target_file, encoding="utf-8") as f:
                    if target_file.suffix in (".yaml", ".yml"):
                        config_dict = yaml.safe_load(f) or {}
                    elif target_file.suffix == ".json":
                        config_dict = json.load(f) or {}
                    else:
                        raise ConfigurationException(
                            f"Unsupported file format: {target_file.suffix}"
                        )
            except Exception as e:
                raise ConfigurationException(f"Failed to parse config file: {e}") from e

        # Substitute environment variables placeholders (e.g. ${VAR})
        config_dict = self._substitute_env_vars(config_dict)

        # Merge WEBPULSE__ env vars
        config_dict = self._merge_env_vars(config_dict)

        # Apply profile configuration if active
        profile_name = config_dict.get("profile", "default")
        if profile_name in PROFILES:
            config_dict = self._merge_dicts(PROFILES[profile_name], config_dict)

        try:
            self._current_config = AppConfig.model_validate(config_dict)
        except ValidationError as e:
            raise ConfigurationException(f"Configuration validation failed: {e}") from e

        return self._current_config

    def get_module_config(self, module_name: str) -> dict[str, Any]:
        """Extract configurations sub-dictionary for an auditing module.

        Args:
            module_name: The name of the module (e.g. 'security', 'seo').

        Returns:
            The module configurations as a dictionary.

        Raises:
            ConfigurationException: If configuration has not been loaded.
        """
        if not self._current_config:
            raise ConfigurationException("Configuration has not been loaded.")

        modules = self._current_config.modules
        if hasattr(modules, module_name):
            module_model = getattr(modules, module_name)
            res_dict: dict[str, Any] = module_model.model_dump()
            return res_dict

        return {}

    def _substitute_env_vars(self, data: Any) -> Any:
        """Replace environment variable patterns in configuration values recursively."""
        if isinstance(data, dict):
            return {k: self._substitute_env_vars(v) for k, v in data.items()}
        if isinstance(data, list):
            return [self._substitute_env_vars(item) for item in data]
        if isinstance(data, str):
            pattern = re.compile(r"\$\{(\w+)\}|\$(\w+)")

            def repl(match: re.Match[str]) -> str:
                var_name = match.group(1) or match.group(2)
                return os.environ.get(var_name, "")

            return pattern.sub(repl, data)
        return data

    def _merge_env_vars(self, config_dict: dict[str, Any]) -> dict[str, Any]:
        """Overlay environment variables prefixed with WEBPULSE__ into config_dict."""
        resolved = copy.deepcopy(config_dict)
        for env_key, val in os.environ.items():
            if env_key.startswith("WEBPULSE__"):
                parts = [p.lower() for p in env_key.split("__")[1:]]
                if not parts:
                    continue

                current = resolved
                for part in parts[:-1]:
                    if part not in current or not isinstance(current[part], dict):
                        current[part] = {}
                    current = current[part]

                last_key = parts[-1]
                coerced_val: Any = val
                if val.lower() == "true":
                    coerced_val = True
                elif val.lower() == "false":
                    coerced_val = False
                else:
                    try:
                        coerced_val = int(val)
                    except ValueError:
                        try:
                            coerced_val = float(val)
                        except ValueError:
                            pass
                current[last_key] = coerced_val
        return resolved

    def _merge_dicts(
        self, default_dict: dict[str, Any], override_dict: dict[str, Any]
    ) -> dict[str, Any]:
        """Perform deep merge of two dictionaries."""
        merged = dict(default_dict)
        for k, v in override_dict.items():
            if k in merged and isinstance(merged[k], dict) and isinstance(v, dict):
                merged[k] = self._merge_dicts(merged[k], v)
            else:
                merged[k] = v
        return merged
