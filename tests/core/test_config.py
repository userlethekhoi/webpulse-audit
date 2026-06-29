import os
from pathlib import Path

import pytest
import yaml

from webpulse.core.config import ConfigManager, ConfigurationException
from webpulse.core.di import Container
from webpulse.core.exceptions import WebPulseException
from webpulse.utils.logging import setup_logging


def test_exceptions() -> None:
    """Test custom exceptions inherit from WebPulseException and stringify correctly."""
    ex = WebPulseException("base error")
    assert str(ex) == "WebPulseException: base error"
    assert ex.message == "base error"


def test_default_config(tmp_path: Path) -> None:
    """Test loading configuration from a standard YAML file compiles defaults correctly."""
    config_data = {"core": {"rate_limit": 20, "max_connections": 40}}
    config_file = tmp_path / "webpulse.yaml"
    with open(config_file, "w", encoding="utf-8") as f:
        yaml.dump(config_data, f)

    manager = ConfigManager()
    config = manager.load_config(config_file)
    assert config.core.rate_limit == 20
    assert config.core.max_connections == 40
    assert config.core.timeout == 12  # preserves base defaults

    sec_config = manager.get_module_config("security")
    assert sec_config["enabled"] is True
    assert "/.env" in sec_config["check_paths"]


def test_config_validation_failures(tmp_path: Path) -> None:
    """Test Pydantic validator limits (such as rate limits and timeouts)."""
    # Rate limit exceeding 200 threshold ceiling
    config_file = tmp_path / "invalid_rate.yaml"
    with open(config_file, "w", encoding="utf-8") as f:
        yaml.dump({"core": {"rate_limit": 250}}, f)

    manager = ConfigManager()
    with pytest.raises(ConfigurationException):
        manager.load_config(config_file)

    # Timeout under 1 second floor
    config_file2 = tmp_path / "invalid_timeout.yaml"
    with open(config_file2, "w", encoding="utf-8") as f:
        yaml.dump({"core": {"timeout": 0}}, f)

    with pytest.raises(ConfigurationException):
        manager.load_config(config_file2)


def test_environment_substitution(tmp_path: Path) -> None:
    """Test placeholder strings (e.g. ${VAR}) are successfully substituted from env variables."""
    os.environ["WEBPULSE_TEST_USER"] = "admin_agent"
    config_data = {"auth": {"credentials": {"username": "${WEBPULSE_TEST_USER}"}}}
    config_file = tmp_path / "env_sub.yaml"
    with open(config_file, "w", encoding="utf-8") as f:
        yaml.dump(config_data, f)

    manager = ConfigManager()
    config = manager.load_config(config_file)
    assert config.auth.credentials["username"] == "admin_agent"

    # Cleanup env variable
    del os.environ["WEBPULSE_TEST_USER"]


def test_double_underscore_env_overrides(tmp_path: Path) -> None:
    """Test env vars overlay correctly into config structures using double underscores."""
    os.environ["WEBPULSE__CORE__RATE_LIMIT"] = "99"
    os.environ["WEBPULSE__CORE__SANDBOX_PLUGINS"] = "false"
    os.environ["WEBPULSE__CORE__TIMEOUT"] = "25"

    config_file = tmp_path / "test.yaml"
    with open(config_file, "w", encoding="utf-8") as f:
        yaml.dump({"core": {"rate_limit": 10}}, f)

    manager = ConfigManager()
    config = manager.load_config(config_file)

    assert config.core.rate_limit == 99
    assert config.core.sandbox_plugins is False
    assert config.core.timeout == 25

    del os.environ["WEBPULSE__CORE__RATE_LIMIT"]
    del os.environ["WEBPULSE__CORE__SANDBOX_PLUGINS"]
    del os.environ["WEBPULSE__CORE__TIMEOUT"]


def test_profile_activation(tmp_path: Path) -> None:
    """Test that specifying a profile preset automatically loads corresponding parameters."""
    config_file = tmp_path / "profile.yaml"
    with open(config_file, "w", encoding="utf-8") as f:
        yaml.dump({"profile": "fast"}, f)

    manager = ConfigManager()
    config = manager.load_config(config_file)
    assert config.core.rate_limit == 50
    assert config.core.max_connections == 100
    assert config.modules.accessibility.enabled is False


def test_dependency_injection() -> None:
    """Test service registration and lookup inside the central DI container."""
    container = Container()
    assert isinstance(container.config_manager, ConfigManager)

    class MockService:
        pass

    mock_inst = MockService()
    container.register("mock_service", mock_inst)
    assert container.get("mock_service") is mock_inst

    with pytest.raises(KeyError):
        container.get("non_existent")


def test_logging_setup() -> None:
    """Test logger setup helper functions compile without raising warnings/errors."""
    setup_logging()
