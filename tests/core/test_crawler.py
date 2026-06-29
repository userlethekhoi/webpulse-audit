import pytest
import respx
from httpx import Response

from webpulse.core.crawler import BFSWebCrawler
from webpulse.reports.schemas import Target
from webpulse.utils.network import AsyncNetworkClient


@pytest.mark.asyncio
async def test_crawler_bfs_scans_internal_links():
    """Verify that crawler only traverses allowed internal domains and handles bounds."""
    client = AsyncNetworkClient(allow_private_ips=True)

    try:
        with respx.mock:
            # Mock pages
            respx.get("https://example.com/").mock(
                return_value=Response(
                    200,
                    text='<html><body><a href="/about">About</a><a href="https://google.com">Google</a></body></html>',
                )
            )
            respx.get("https://example.com/about").mock(
                return_value=Response(
                    200,
                    text='<html><body><a href="/contact">Contact</a></body></html>',
                )
            )
            respx.get("https://example.com/contact").mock(
                return_value=Response(
                    200,
                    text="<html><body>Contact Page</body></html>",
                )
            )

            # Max Depth = 2, Max Pages = 5
            crawler = BFSWebCrawler(
                max_depth=2,
                max_pages=5,
                allowed_domains=["example.com"],
            )

            root = Target(url="https://example.com/")
            discovered = await crawler.crawl(root, client)

            urls = [t.url for t in discovered]
            # Should crawl root, about, contact. Should NOT crawl external Google.
            assert "https://example.com/" in urls
            assert "https://example.com/about" in urls
            assert "https://example.com/contact" in urls
            assert "https://google.com" not in urls
            assert len(discovered) == 3

    finally:
        await client.close()


@pytest.mark.asyncio
async def test_crawler_respects_max_pages_limit():
    """Verify that crawler stops scanning after max_pages limit is reached."""
    client = AsyncNetworkClient(allow_private_ips=True)

    try:
        with respx.mock:
            respx.get("https://example.com/").mock(
                return_value=Response(
                    200,
                    text='<html><body><a href="/1">1</a><a href="/2">2</a><a href="/3">3</a></body></html>',
                )
            )
            respx.get("https://example.com/1").mock(return_value=Response(200, text=""))
            respx.get("https://example.com/2").mock(return_value=Response(200, text=""))

            # Page limit = 2
            crawler = BFSWebCrawler(
                max_depth=2,
                max_pages=2,
                allowed_domains=["example.com"],
            )

            root = Target(url="https://example.com/")
            discovered = await crawler.crawl(root, client)

            assert len(discovered) == 2

    finally:
        await client.close()


@pytest.mark.asyncio
async def test_crawler_respects_depth_limit():
    """Verify that crawler stops scanning at depth boundary limit."""
    client = AsyncNetworkClient(allow_private_ips=True)

    try:
        with respx.mock:
            respx.get("https://example.com/").mock(
                return_value=Response(
                    200,
                    text='<html><body><a href="/1">1</a></body></html>',
                )
            )
            respx.get("https://example.com/1").mock(
                return_value=Response(
                    200,
                    text='<html><body><a href="/2">2</a></body></html>',
                )
            )
            respx.get("https://example.com/2").mock(return_value=Response(200, text=""))

            # Depth = 1 (can discover 1, but NOT 2)
            crawler = BFSWebCrawler(
                max_depth=1,
                max_pages=10,
                allowed_domains=["example.com"],
            )

            root = Target(url="https://example.com/")
            discovered = await crawler.crawl(root, client)

            urls = [t.url for t in discovered]
            assert "https://example.com/" in urls
            assert "https://example.com/1" in urls
            assert "https://example.com/2" not in urls
            assert len(discovered) == 2

    finally:
        await client.close()


@pytest.mark.asyncio
async def test_crawler_respects_exclude_patterns():
    """Verify that crawler avoids urls matching exclude regexes."""
    client = AsyncNetworkClient(allow_private_ips=True)

    try:
        with respx.mock:
            respx.get("https://example.com/").mock(
                return_value=Response(
                    200,
                    text='<html><body><a href="/about">About</a><a href="/logout">Logout</a></body></html>',
                )
            )
            respx.get("https://example.com/about").mock(return_value=Response(200, text=""))

            crawler = BFSWebCrawler(
                max_depth=2,
                max_pages=10,
                allowed_domains=["example.com"],
                exclude_patterns=[r"/logout", r"\.pdf$"],
            )

            root = Target(url="https://example.com/")
            discovered = await crawler.crawl(root, client)

            urls = [t.url for t in discovered]
            assert "https://example.com/about" in urls
            assert "https://example.com/logout" not in urls

    finally:
        await client.close()
