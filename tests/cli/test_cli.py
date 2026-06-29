import argparse
from pathlib import Path
import pytest

from webpulse.cli.main import coerce_value, create_parser


def test_cli_parser_creation():
    """Verify that argparse parses arguments correctly for WebPulse."""
    parser = create_parser()
    assert isinstance(parser, argparse.ArgumentParser)

    # Test scan args
    args = parser.parse_args(["scan", "https://example.com", "-p", "fast", "--crawl"])
    assert args.command == "scan"
    assert args.target_url == "https://example.com"
    assert args.profile == "fast"
    assert args.crawl is True

    # Test config show args
    args = parser.parse_args(["config", "show"])
    assert args.command == "config"
    assert args.subcommand == "show"

    # Test plugins list args
    args = parser.parse_args(["plugins", "list"])
    assert args.command == "plugins"
    assert args.subcommand == "list"


def test_cli_coerce_values():
    """Verify that CLI string input is coerced to correct types."""
    assert coerce_value("true") is True
    assert coerce_value("FALSE") is False
    assert coerce_value("123") == 123
    assert coerce_value("3.14") == 3.14
    assert coerce_value("some-string") == "some-string"


@pytest.mark.asyncio
async def test_cli_report_filename_sanitization(tmp_path):
    """Verify that the generated report filename is sanitized from illegal Windows characters."""
    from unittest.mock import AsyncMock, MagicMock, patch
    from webpulse.cli.main import handle_scan
    from webpulse.core.config import AppConfig

    # Mock AsyncNetworkClient to return a dummy response
    mock_client_instance = MagicMock()
    mock_client_instance.request = AsyncMock(
        return_value=MagicMock(status_code=200, headers={}, text="<html></html>")
    )
    mock_client_instance.close = AsyncMock()

    written_paths = []

    def mock_write(self, text, *args, **kwargs):
        written_paths.append(str(self))
        return len(text)

    # Mock PluginLoader to return empty list of plugins
    with patch("webpulse.cli.main.AsyncNetworkClient", return_value=mock_client_instance), \
         patch("webpulse.cli.main.PluginLoader.discover_plugins", return_value=[]), \
         patch("webpulse.cli.main.Path.write_text", new=mock_write):

        args = argparse.Namespace(
            target_url="https://yinhing.com.hk/listing-en.php?category_id=9",
            format="json",
            output=None,
        )
        config = AppConfig()
        config.reporting.output_dir = str(tmp_path)
        config.reporting.formats = ["json"]

        res = await handle_scan(args, config)
        assert res == 0

        # Verify that write_text was called
        assert len(written_paths) > 0

        # The filename should not contain illegal characters like '?' or ':'
        for path_str in written_paths:
            filename = Path(path_str).name
            assert "?" not in filename
            assert ":" not in filename



