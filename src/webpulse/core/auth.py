"""Session authentication coordinator for WebPulse.

Executes login actions (POST JSON, Form) and manages session credentials injection.
"""

import logging
from typing import Any

from webpulse.utils.network import AsyncNetworkClient

logger = logging.getLogger("webpulse.core.auth")


class AuthCoordinator:
    """Orchestrates session login requests and headers/cookies injection."""

    def __init__(self, auth_config: dict[str, Any]) -> None:
        """Initialize the AuthCoordinator.

        Args:
            auth_config: Authentication parameters from configuration.
        """
        self.config = auth_config
        self.enabled = auth_config.get("enabled", False)
        self.login_url = auth_config.get("login_url")
        self.method = auth_config.get("method", "post_json")
        self.credentials = auth_config.get("credentials", {})
        self.token_injection = auth_config.get("token_injection", {})
        self._token_val: str | None = None

    async def establish_session(self, client: AsyncNetworkClient) -> bool:
        """Send login requests to target endpoint and save session tokens.

        Args:
            client: Secure network HTTPX connection client.

        Returns:
            True if session is established or auth is disabled; False otherwise.
        """
        if not self.enabled:
            return True

        if not self.login_url and self.method != "headers":
            logger.warning("Auth is enabled but login_url is not configured.")
            return False

        if self.method == "headers":
            logger.info("Auth method set to headers. No login request needed.")
            return True

        assert self.login_url is not None

        try:
            logger.info(f"Establishing auth session via {self.method} at {self.login_url}...")

            if self.method == "post_json":
                response = await client.request("POST", self.login_url, json=self.credentials)
            elif self.method == "post_form":
                response = await client.request("POST", self.login_url, data=self.credentials)
            else:
                logger.warning(f"Unsupported auth method: {self.method}")
                return False

            if response.status_code >= 400:
                logger.error(
                    f"Login failed with HTTP status {response.status_code}: {response.text}"
                )
                return False

            # Extract token if token_injection is configured
            token_name = self.token_injection.get("name")
            if token_name:
                # 1. Try response JSON body
                try:
                    res_data = response.json()
                    if isinstance(res_data, dict) and token_name in res_data:
                        self._token_val = str(res_data[token_name])
                        logger.info(f"Extracted auth token '{token_name}' from response JSON body.")
                except Exception as e:
                    logger.debug(f"Response is not valid JSON for token extraction: {e}")

                # 2. Try response cookies
                if not self._token_val:
                    cookie_val = response.cookies.get(token_name)
                    if cookie_val:
                        self._token_val = cookie_val
                        logger.info(f"Extracted auth cookie '{token_name}' from response cookies.")

            logger.info("Authentication session established successfully.")
            return True

        except Exception as e:
            logger.error(f"Authentication exception encountered: {e}")
            return False

    def inject_headers(self, headers: dict[str, str]) -> dict[str, str]:
        """Inject auth credentials/tokens into outbound request headers.

        Args:
            headers: Base request headers.

        Returns:
            Dictionary containing updated headers.
        """
        if not self.enabled:
            return headers

        injected = dict(headers)

        # 1. If method is headers, inject credentials directly as headers
        if self.method == "headers":
            for k, v in self.credentials.items():
                injected[k] = v
            return injected

        # 2. If token is extracted, inject it
        if self._token_val:
            token_name = self.token_injection.get("name", "Authorization")
            token_type = self.token_injection.get("type", "cookie")

            if token_type == "header":
                if token_name.lower() == "authorization" and not self._token_val.lower().startswith(
                    "bearer "
                ):
                    injected[token_name] = f"Bearer {self._token_val}"
                else:
                    injected[token_name] = self._token_val
            elif token_type == "cookie":
                existing_cookie = injected.get("Cookie", "")
                cookie_str = f"{token_name}={self._token_val}"
                if existing_cookie:
                    injected["Cookie"] = f"{existing_cookie}; {cookie_str}"
                else:
                    injected["Cookie"] = cookie_str

        return injected
