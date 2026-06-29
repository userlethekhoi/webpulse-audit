import pytest
import respx
from httpx import Response

from webpulse.core.auth import AuthCoordinator
from webpulse.utils.network import AsyncNetworkClient


@pytest.mark.asyncio
async def test_auth_headers_injection():
    """Verify that headers method directly injects config credentials into headers."""
    auth_config = {
        "enabled": True,
        "method": "headers",
        "credentials": {
            "Authorization": "Bearer some-static-secret-token",
            "X-Custom-Client": "WebPulse",
        },
    }

    auth = AuthCoordinator(auth_config)
    client = AsyncNetworkClient(allow_private_ips=True)

    try:
        success = await auth.establish_session(client)
        assert success is True

        headers = auth.inject_headers({"Host": "example.com"})
        assert headers["Authorization"] == "Bearer some-static-secret-token"
        assert headers["X-Custom-Client"] == "WebPulse"
        assert headers["Host"] == "example.com"
    finally:
        await client.close()


@pytest.mark.asyncio
async def test_auth_post_json_token_extraction():
    """Verify that JSON login works and extracts token from response body."""
    auth_config = {
        "enabled": True,
        "login_url": "https://example.com/api/login",
        "method": "post_json",
        "credentials": {"user": "admin", "pass": "secret"},
        "token_injection": {
            "type": "header",
            "name": "Authorization",
        },
    }

    auth = AuthCoordinator(auth_config)
    client = AsyncNetworkClient(allow_private_ips=True)

    try:
        with respx.mock:
            # Mock login endpoint
            respx.post("https://example.com/api/login").mock(
                return_value=Response(
                    200,
                    json={"Authorization": "my-json-response-token"},
                )
            )

            success = await auth.establish_session(client)
            assert success is True
            assert auth._token_val == "my-json-response-token"

            headers = auth.inject_headers({})
            assert headers["Authorization"] == "Bearer my-json-response-token"
    finally:
        await client.close()


@pytest.mark.asyncio
async def test_auth_cookie_token_extraction():
    """Verify that cookies login extracts cookie token from response."""
    auth_config = {
        "enabled": True,
        "login_url": "https://example.com/api/login",
        "method": "post_form",
        "credentials": {"user": "admin", "pass": "secret"},
        "token_injection": {
            "type": "cookie",
            "name": "session_id",
        },
    }

    auth = AuthCoordinator(auth_config)
    client = AsyncNetworkClient(allow_private_ips=True)

    try:
        with respx.mock:
            respx.post("https://example.com/api/login").mock(
                return_value=Response(
                    200,
                    headers={"Set-Cookie": "session_id=extracted-cookie-value; Path=/"},
                )
            )

            success = await auth.establish_session(client)
            assert success is True
            assert auth._token_val == "extracted-cookie-value"

            headers = auth.inject_headers({})
            assert headers["Cookie"] == "session_id=extracted-cookie-value"
    finally:
        await client.close()
