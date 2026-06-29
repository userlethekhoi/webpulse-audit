"""Asynchronous HTML DOM parser for WebPulse.

Wraps BeautifulSoup4 parsing logic inside event loop threadpool executors to prevent blocking.
"""

import asyncio

from bs4 import BeautifulSoup


class AsyncHTMLParser:
    """Non-blocking HTML DOM parser wrapper."""

    @staticmethod
    async def parse_dom(html_content: str) -> BeautifulSoup:
        """Parse raw HTML content into a BeautifulSoup DOM tree asynchronously.

        Args:
            html_content: Raw HTML text string.

        Returns:
            BeautifulSoup object parsed using the 'html.parser' backend.
        """
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, lambda: BeautifulSoup(html_content, "html.parser"))
