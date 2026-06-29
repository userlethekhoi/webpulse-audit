import argparse

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
