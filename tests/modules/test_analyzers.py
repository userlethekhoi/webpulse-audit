"""Unit and integration tests for WebPulse built-in analyzer plugins."""

from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock

import httpx
import pytest
import respx

from webpulse.modules.http.plugin import HttpPlugin
from webpulse.modules.security.plugin import SecurityPlugin
from webpulse.modules.seo.plugin import SeoPlugin
from webpulse.modules.ssl.plugin import SslPlugin
from webpulse.reports.schemas import Severity, Target
from webpulse.utils.network import AsyncNetworkClient


@pytest.mark.asyncio
@respx.mock
async def test_http_analyzer_success() -> None:
    """Verify HTTP analyzer handles a perfect compressed HTTP/2 response with no findings."""
    client = AsyncNetworkClient(allow_private_ips=True)
    client._resolve_host = AsyncMock(return_value=["127.0.0.1"])  # type: ignore

    respx.get("https://example.com/").mock(
        return_value=httpx.Response(
            200,
            headers={"Content-Encoding": "br"},
            extensions={"http_version": b"HTTP/2"},
        )
    )

    plugin = HttpPlugin()
    target = Target(url="https://example.com/")
    findings = await plugin.execute(target, client)

    # 0 findings expected since it has Brotli compression, HTTP/2, and 200 OK status
    assert len(findings) == 0
    await client.close()


@pytest.mark.asyncio
@respx.mock
async def test_http_analyzer_deficiencies() -> None:
    """Verify HTTP analyzer flags uncompressed HTTP/1.1 connection and server errors."""
    client = AsyncNetworkClient(allow_private_ips=True)
    client._resolve_host = AsyncMock(return_value=["127.0.0.1"])  # type: ignore

    # 1. Uncompressed HTTP/1.1 response
    respx.get("https://example.com/uncompressed").mock(
        return_value=httpx.Response(200, extensions={"http_version": b"HTTP/1.1"})
    )

    plugin = HttpPlugin()
    target = Target(url="https://example.com/uncompressed")
    findings = await plugin.execute(target, client)

    titles = [f.title for f in findings]
    assert "HTTP Compression Disabled" in titles
    assert "HTTP/2 Protocol Not Supported" in titles

    # 2. Server Error status code response
    respx.get("https://example.com/error").mock(
        return_value=httpx.Response(503, extensions={"http_version": b"HTTP/2"})
    )
    target_err = Target(url="https://example.com/error")
    findings_err = await plugin.execute(target_err, client)

    titles_err = [f.title for f in findings_err]
    assert "Server Response Error Code Returned" in titles_err
    await client.close()


@pytest.mark.asyncio
async def test_ssl_analyzer_expiring_soon() -> None:
    """Verify SSL analyzer detects certificates expiring soon."""
    client = AsyncNetworkClient(allow_private_ips=True)
    client._resolve_host = AsyncMock(return_value=["127.0.0.1"])  # type: ignore

    expiry = datetime.now(UTC) + timedelta(days=5)
    mock_cert_info = {
        "valid": True,
        "expiry_date": expiry.isoformat(),
        "subject": {"CN": "example.com"},
        "issuer": {"O": "Let's Encrypt"},
        "serial_number": "12345",
    }
    client.check_ssl = AsyncMock(return_value=mock_cert_info)  # type: ignore

    plugin = SslPlugin()
    # Configure custom verification threshold of 10 days
    await plugin.on_load({"verify_expiry_days": 10})

    target = Target(url="https://example.com/")
    findings = await plugin.execute(target, client)

    assert len(findings) == 1
    assert findings[0].title == "SSL Certificate Expiring Soon"
    assert findings[0].severity == Severity.HIGH
    await client.close()


@pytest.mark.asyncio
async def test_ssl_analyzer_expired() -> None:
    """Verify SSL analyzer flags invalid/expired certificates."""
    client = AsyncNetworkClient(allow_private_ips=True)
    client._resolve_host = AsyncMock(return_value=["127.0.0.1"])  # type: ignore

    mock_cert_info = {
        "valid": False,
        "expiry_date": (datetime.now(UTC) - timedelta(days=1)).isoformat(),
    }
    client.check_ssl = AsyncMock(return_value=mock_cert_info)  # type: ignore

    plugin = SslPlugin()
    target = Target(url="https://example.com/")
    findings = await plugin.execute(target, client)

    assert len(findings) == 1
    assert findings[0].title == "SSL Certificate Expired or Invalid"
    assert findings[0].severity == Severity.CRITICAL
    await client.close()


@pytest.mark.asyncio
@respx.mock
async def test_seo_analyzer_violations() -> None:
    """Verify SEO analyzer spots title, description, h1 headings, and canonical violations."""
    client = AsyncNetworkClient(allow_private_ips=True)
    client._resolve_host = AsyncMock(return_value=["127.0.0.1"])  # type: ignore

    html_content = """
    <html>
      <head>
        <title>Short</title>
      </head>
      <body>
        <h1>Heading 1</h1>
        <h1>Duplicate Heading 1</h1>
        <img src="logo.png" />
      </body>
    </html>
    """
    respx.get("https://example.com/seo-fail").mock(
        return_value=httpx.Response(200, html=html_content)
    )

    plugin = SeoPlugin()
    target = Target(url="https://example.com/seo-fail")
    findings = await plugin.execute(target, client)

    titles = [f.title for f in findings]
    assert "Page Title Length Out of Optimal Bounds" in titles
    assert "Missing Meta Description Header" in titles
    assert "Duplicate H1 Headings Detected" in titles
    assert "Images Missing Alt Attributes" in titles
    assert "Missing Canonical Link Reference" in titles
    await client.close()


@pytest.mark.asyncio
@respx.mock
async def test_security_analyzer_exposed_files() -> None:
    """Verify security analyzer flags missing security headers and exposed configuration files."""
    client = AsyncNetworkClient(allow_private_ips=True)
    client._resolve_host = AsyncMock(return_value=["127.0.0.1"])  # type: ignore

    # 1. Main request: returns index page but lacks CSP, HSTS, X-Frame-Options, nosniff
    respx.get("https://example.com/").mock(
        return_value=httpx.Response(
            200,
            headers={"Set-Cookie": "session=secret"},
        )
    )

    # 2. Exposed Git endpoint probe
    respx.get("https://example.com/.git/HEAD").mock(
        return_value=httpx.Response(200, text="ref: refs/heads/main")
    )

    # 3. Exposed .env file probe
    respx.get("https://example.com/.env").mock(
        return_value=httpx.Response(200, text="DB_PASSWORD=secret_db_pass\nPORT=80")
    )

    plugin = SecurityPlugin()
    target = Target(url="https://example.com/")
    findings = await plugin.execute(target, client)

    titles = [f.title for f in findings]
    assert "Missing Content-Security-Policy Header" in titles
    assert "Missing Strict-Transport-Security Header" in titles
    assert "Missing Anti-Clickjacking Header" in titles
    assert "Missing or Invalid X-Content-Type-Options Header" in titles
    assert "Insecure Cookie Flags Detected" in titles
    assert "Exposed Git Repository Directory Detected" in titles
    assert "Exposed System Environment File Detected" in titles
    await client.close()


# ── SQL Injection Detection Tests ───────────────────────────────────────────


@pytest.mark.asyncio
@respx.mock
async def test_sqli_error_based_mysql_detection() -> None:
    """Verify SQLi error-based detection flags MySQL error in response."""
    client = AsyncNetworkClient(allow_private_ips=True)
    client._resolve_host = AsyncMock(return_value=["127.0.0.1"])  # type: ignore

    target_url = "https://example.com/products?id=1"

    # Mock main page request
    respx.get(target_url).mock(
        return_value=httpx.Response(200, html="<html><body>Product page</body></html>")
    )

    # Mock SQLi-injected request returning MySQL error
    injected_url = "https://example.com/products?id=1%27"
    respx.get(injected_url).mock(
        return_value=httpx.Response(
            200,
            text="You have an error in your SQL syntax; check the manual that corresponds "
            "to your MySQL server version for the right syntax to use near ''1''' at line 1",
        )
    )

    plugin = SecurityPlugin()
    await plugin.on_load({"sqli_check": True, "sqli_timeout": 5})
    target = Target(url=target_url)
    findings = await plugin.execute(target, client)

    sqli_titles = [f.title for f in findings if "SQL Injection" in f.title]
    assert len(sqli_titles) >= 1, f"Expected SQLi findings, got titles: {[f.title for f in findings]}"
    assert any("Error-Based" in t for t in sqli_titles)
    assert any("MySQL" in t for t in sqli_titles)
    assert any(f.severity == Severity.CRITICAL for f in findings if "SQL Injection" in f.title)
    await client.close()


@pytest.mark.asyncio
@respx.mock
async def test_sqli_error_based_postgresql_detection() -> None:
    """Verify SQLi error-based detection flags PostgreSQL error in response."""
    client = AsyncNetworkClient(allow_private_ips=True)
    client._resolve_host = AsyncMock(return_value=["127.0.0.1"])  # type: ignore

    target_url = "https://example.com/items?category_id=5"

    respx.get(target_url).mock(
        return_value=httpx.Response(200, html="<html><body>Items</body></html>")
    )

    # Mock SQLi-injected request returning PostgreSQL error
    injected_url = "https://example.com/items?category_id=5%27"
    respx.get(injected_url).mock(
        return_value=httpx.Response(
            200,
            text="ERROR:  syntax error at or near \"'\"\nLINE 1: SELECT * FROM items WHERE category_id=5'\n"
            "org.postgresql.util.PSQLException: ERROR",
        )
    )

    plugin = SecurityPlugin()
    await plugin.on_load({"sqli_check": True, "sqli_timeout": 5})
    target = Target(url=target_url)
    findings = await plugin.execute(target, client)

    sqli_titles = [f.title for f in findings if "SQL Injection" in f.title]
    assert len(sqli_titles) >= 1
    assert any("PostgreSQL" in t for t in sqli_titles)
    await client.close()


@pytest.mark.asyncio
@respx.mock
async def test_sqli_boolean_blind_detection() -> None:
    """Verify boolean-blind SQLi detection via response size difference."""
    client = AsyncNetworkClient(allow_private_ips=True)
    client._resolve_host = AsyncMock(return_value=["127.0.0.1"])  # type: ignore

    target_url = "https://example.com/news?id=100"

    # Main page
    respx.get(target_url).mock(
        return_value=httpx.Response(200, html="<html><body>News article</body></html>")
    )

    # Boolean-true: returns full page
    true_url = "https://example.com/news?id=100%27+AND+%271%27%3D%271"
    respx.get(true_url).mock(
        return_value=httpx.Response(200, text="<html>" + "A" * 2000 + "</html>")
    )

    # Boolean-false: returns short/empty page
    false_url = "https://example.com/news?id=100%27+AND+%271%27%3D%272"
    respx.get(false_url).mock(
        return_value=httpx.Response(200, text="<html></html>")
    )

    plugin = SecurityPlugin()
    await plugin.on_load({"sqli_check": True, "sqli_timeout": 5})
    target = Target(url=target_url)
    findings = await plugin.execute(target, client)

    sqli_titles = [f.title for f in findings if "SQL Injection" in f.title]
    assert len(sqli_titles) >= 1, f"Expected boolean-blind SQLi finding, got: {sqli_titles}"
    assert any("Boolean-Based Blind" in t for t in sqli_titles)
    await client.close()


@pytest.mark.asyncio
@respx.mock
async def test_sqli_no_false_positive_on_clean_url() -> None:
    """Verify no SQLi false positives on a clean URL with query parameters."""
    client = AsyncNetworkClient(allow_private_ips=True)
    client._resolve_host = AsyncMock(return_value=["127.0.0.1"])  # type: ignore

    target_url = "https://example.com/search?q=hello&page=1"

    # Mock all requests with clean responses (no SQL errors, same response size)
    def clean_response(request: httpx.Request) -> httpx.Response:  # noqa: ARG001 # type: ignore[type-arg]
        return httpx.Response(200, text="<html><body>Search results</body></html>")

    respx.route(method="GET", url__startswith="https://example.com/search").mock(
        side_effect=clean_response
    )

    plugin = SecurityPlugin()
    await plugin.on_load({"sqli_check": True, "sqli_timeout": 5})
    target = Target(url=target_url)
    findings = await plugin.execute(target, client)

    sqli_titles = [f.title for f in findings if "SQL Injection" in f.title]
    assert len(sqli_titles) == 0, f"False positive SQLi findings: {sqli_titles}"
    await client.close()


@pytest.mark.asyncio
@respx.mock
async def test_sqli_disabled_by_config() -> None:
    """Verify SQLi checks are skipped when sqli_check is False."""
    client = AsyncNetworkClient(allow_private_ips=True)
    client._resolve_host = AsyncMock(return_value=["127.0.0.1"])  # type: ignore

    target_url = "https://example.com/products?id=1"

    # Mock main page
    respx.get(target_url).mock(
        return_value=httpx.Response(200, html="<html><body>Product</body></html>")
    )

    plugin = SecurityPlugin()
    await plugin.on_load({"sqli_check": False})
    target = Target(url=target_url)
    findings = await plugin.execute(target, client)

    sqli_titles = [f.title for f in findings if "SQL Injection" in f.title]
    assert len(sqli_titles) == 0
    await client.close()


@pytest.mark.asyncio
@respx.mock
async def test_sqli_no_query_params() -> None:
    """Verify SQLi checks gracefully handle URLs with no query parameters."""
    client = AsyncNetworkClient(allow_private_ips=True)
    client._resolve_host = AsyncMock(return_value=["127.0.0.1"])  # type: ignore

    target_url = "https://example.com/about"

    respx.get(target_url).mock(
        return_value=httpx.Response(
            200,
            html="<html><body>About page</body></html>",
            headers={"Content-Security-Policy": "default-src 'self'"},
        )
    )

    plugin = SecurityPlugin()
    await plugin.on_load({"sqli_check": True})
    target = Target(url=target_url)
    findings = await plugin.execute(target, client)

    sqli_titles = [f.title for f in findings if "SQL Injection" in f.title]
    assert len(sqli_titles) == 0
    # Should still perform header checks (CSP is present → no CSP finding)
    assert "Missing Content-Security-Policy Header" not in [f.title for f in findings]
    await client.close()
