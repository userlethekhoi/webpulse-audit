"""Breadth-First Search (BFS) crawling engine for WebPulse.

Traverses internal website links up to configured depth and page boundaries.
"""

import logging
import re
from urllib.parse import parse_qsl, urlencode, urljoin, urlparse

from webpulse.reports.schemas import Target
from webpulse.utils.network import AsyncNetworkClient
from webpulse.utils.parser import AsyncHTMLParser

logger = logging.getLogger("webpulse.core.crawler")


class BFSWebCrawler:
    """Async breadth-first search crawler for discovered internal pages."""

    def __init__(
        self,
        max_depth: int,
        max_pages: int,
        allowed_domains: list[str],
        exclude_patterns: list[str] | None = None,
    ) -> None:
        """Initialize the BFSWebCrawler.

        Args:
            max_depth: Maximum recursion depth (0 for root page only).
            max_pages: Maximum count of unique targets to scan.
            allowed_domains: Target domains allowed for crawling.
            exclude_patterns: List of regex strings to ignore.
        """
        self.max_depth = max_depth
        self.max_pages = max_pages
        self.allowed_domains = [domain.lower() for domain in allowed_domains]

        # Compile exclude regex patterns
        self.exclude_regexes = []
        if exclude_patterns:
            for pattern in exclude_patterns:
                try:
                    self.exclude_regexes.append(re.compile(pattern))
                except re.error as e:
                    logger.warning(f"Invalid crawler exclude pattern regex '{pattern}': {e}")

    async def crawl(self, root_target: Target, client: AsyncNetworkClient) -> list[Target]:
        """Audit target site link trees using BFS.

        Args:
            root_target: Root target page configuration.
            client: Secure network HTTPX connection client.

        Returns:
            List of Target objects for all discovered internal URLs.
        """
        root_url = root_target.url
        parsed_root = urlparse(root_url)
        root_domain = parsed_root.netloc.split(":")[0].lower()

        if not self.allowed_domains and root_domain:
            self.allowed_domains = [root_domain]

        standardized_root = self._standardize_url(root_url)
        if not self._is_allowed(standardized_root):
            return [root_target]

        queue: list[tuple[str, int]] = [(standardized_root, 0)]
        visited: set[str] = set()
        targets: list[Target] = []

        while queue and len(targets) < self.max_pages:
            url, depth = queue.pop(0)
            if url in visited:
                continue
            visited.add(url)

            logger.info(f"Crawling URL: {url} (depth: {depth})")
            targets.append(Target(url=url))

            if depth >= self.max_depth:
                continue

            try:
                response = await client.request("GET", url)
                if response.status_code >= 400:
                    logger.warning(
                        f"Crawler received error status {response.status_code} for {url}"
                    )
                    continue

                html_content = response.text
                soup = await AsyncHTMLParser.parse_dom(html_content)

                for a_tag in soup.find_all("a", href=True):
                    href = a_tag.get("href")
                    if not isinstance(href, str):
                        continue
                    resolved_url = urljoin(url, href)
                    standardized_url = self._standardize_url(resolved_url)

                    if (
                        standardized_url not in visited
                        and self._is_allowed(standardized_url)
                        and not any(standardized_url == q[0] for q in queue)
                    ):
                        queue.append((standardized_url, depth + 1))

            except Exception as e:
                logger.error(f"Failed to crawl URL '{url}': {e}")
                continue

        return targets

    def _is_allowed(self, url: str) -> bool:
        """Verify if URL netloc and path are permitted for crawling."""
        try:
            parsed = urlparse(url)
            if parsed.scheme not in ("http", "https"):
                return False

            domain = parsed.netloc.split(":")[0].lower()
            if not any(domain == d or domain.endswith(f".{d}") for d in self.allowed_domains):
                return False

            path_and_query = parsed.path
            if parsed.query:
                path_and_query += f"?{parsed.query}"

            return not any(
                rx.search(url) or rx.search(path_and_query) for rx in self.exclude_regexes
            )
        except Exception:
            return False

    def _standardize_url(self, url: str) -> str:
        """Strip hash fragments, trailing slashes, and sort query parameters."""
        try:
            parsed = urlparse(url)
            scheme = parsed.scheme.lower()
            netloc = parsed.netloc.lower()
            path = parsed.path
            if path.endswith("/") and len(path) > 1:
                path = path[:-1]

            query_params = parse_qsl(parsed.query)
            query_params.sort()
            query = urlencode(query_params) if query_params else ""

            reconstructed = f"{scheme}://{netloc}{path}"
            if query:
                reconstructed += f"?{query}"
            return reconstructed
        except Exception:
            return url
