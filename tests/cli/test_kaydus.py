import argparse
from unittest.mock import AsyncMock, MagicMock, patch
import pytest
import respx
import httpx

from kaydus.cli import _is_url, _slash_completer
from kaydus.commands import (
    get_help_text,
    handle_scan,
    handle_seo,
    handle_security,
    handle_ssl,
    handle_http,
)


def test_kaydus_url_detection():
    """Verify URL detection helper in Kaydus REPL."""
    assert _is_url("example.com") is True
    assert _is_url("https://example.com/path?query=val") is True
    assert _is_url("http://test.org") is True
    assert _is_url("/scan") is False
    assert _is_url("not a url") is False


def test_kaydus_slash_completer():
    """Verify slash command autocomplete generator."""
    # Matches all slash commands starting with /s
    matches_s = _slash_completer("/s")
    assert len(matches_s) > 0
    # Suggestions should be formatted strings
    assert any("scan" in line for line in matches_s)
    assert any("seo" in line for line in matches_s)
    assert any("security" in line for line in matches_s)
    assert any("ssl" in line for line in matches_s)

    # Empty match for non-slash inputs
    assert _slash_completer("help") == []


def test_kaydus_help_text():
    """Verify help menu contents."""
    help_text = get_help_text()
    assert "SCAN COMMANDS" in help_text
    assert "GENERAL COMMANDS" in help_text
    assert "/scan" in help_text
    assert "/seo" in help_text
    assert "/security" in help_text


@pytest.mark.asyncio
@respx.mock
async def test_kaydus_command_handlers():
    """Verify all scan-related handlers execute correctly with mocked HTTP responses."""
    target_url = "https://example.com/"

    # Mock the HTTP calls made by the crawler/scanners
    respx.get(target_url).mock(
        return_value=httpx.Response(
            200,
            html="<html><head><title>Test Title</title></head><body><h1>Heading</h1></body></html>",
            headers={"Content-Encoding": "br"},
            extensions={"http_version": b"HTTP/2"},
        )
    )
    # Mock fallback and other common request patterns
    respx.get("https://example.com/.git/HEAD").mock(
        return_value=httpx.Response(404)
    )
    respx.get("https://example.com/.env").mock(
        return_value=httpx.Response(404)
    )

    # Mock SSL checks
    mock_cert_info = {
        "valid": True,
        "expiry_date": "2026-12-31T23:59:59Z",
        "subject": {"CN": "example.com"},
        "issuer": {"O": "Mock CA"},
        "serial_number": "12345",
    }

    # Patch the AsyncNetworkClient check_ssl and host resolution functions
    with patch("webpulse.utils.network.AsyncNetworkClient.check_ssl", return_value=mock_cert_info), \
         patch("webpulse.utils.network.AsyncNetworkClient._resolve_host", return_value=["127.0.0.1"]):

        # Test /scan
        scan_report = await handle_scan("example.com")
        assert "Scan Report:" in scan_report
        assert "Health Score:" in scan_report

        # Test /seo
        seo_report = await handle_seo("example.com")
        assert "Scan Report:" in seo_report

        # Test /security
        security_report = await handle_security("example.com")
        assert "Scan Report:" in security_report

        # Test /ssl
        ssl_report = await handle_ssl("example.com")
        assert "Scan Report:" in ssl_report

        # Test /http
        http_report = await handle_http("example.com")
        assert "Scan Report:" in http_report
