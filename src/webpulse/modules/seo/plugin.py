"""SEO analyzer plugin for WebPulse.

Evaluates DOM structure elements, metadata tag lengths, missing image alt attributes,
and canonical tags.
"""

from webpulse.modules.base import BasePlugin, PluginMetadata
from webpulse.reports.schemas import Evidence, Finding, Severity, Target
from webpulse.utils.network import AsyncNetworkClient
from webpulse.utils.parser import AsyncHTMLParser


class SeoPlugin(BasePlugin):
    """Built-in SEO Auditor Plugin."""

    @property
    def metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="webpulse-seo-analyzer",
            category="seo",
            version="2.0.0",
        )

    async def execute(self, target: Target, client: AsyncNetworkClient) -> list[Finding]:
        findings: list[Finding] = []

        try:
            # 1. Fetch raw HTML page
            response = await client.request("GET", target.url)
            html_content = response.text

            # 2. Parse DOM asynchronously using AsyncHTMLParser
            soup = await AsyncHTMLParser.parse_dom(html_content)

            # 3. Check Page Title Tag
            title_tag = soup.find("title")
            if not title_tag:
                findings.append(
                    Finding(
                        plugin_name=self.metadata.name,
                        category=self.metadata.category,
                        target_url=target.url,
                        title="Missing Page Title Tag",
                        severity=Severity.MEDIUM,
                        confidence=1.0,
                        description=(
                            "The HTML document lacks a <title> tag. "
                            "Page titles are critical for search engine results listing."
                        ),
                        remediation=(
                            "Add a descriptive <title> tag inside the "
                            "<head> block of the document."
                        ),
                        evidence=[],
                    )
                )
            else:
                title_text = title_tag.get_text().strip()
                length = len(title_text)
                if length < 30 or length > 60:
                    findings.append(
                        Finding(
                            plugin_name=self.metadata.name,
                            category=self.metadata.category,
                            target_url=target.url,
                            title="Page Title Length Out of Optimal Bounds",
                            severity=Severity.LOW,
                            confidence=0.9,
                            description=(
                                f"The page title length is {length} characters. "
                                "Search engines typically truncate page titles that are longer "
                                "than 60 characters, and title tags under 30 characters lack "
                                "keyword optimization."
                            ),
                            remediation=(
                                "Adjust the page title length to be between "
                                "30 and 60 characters."
                            ),
                            evidence=[
                                Evidence(
                                    type="html_snippet",
                                    data=f"Title ({length} chars): '{title_text}'",
                                )
                            ],
                        )
                    )

            # 4. Check Meta Description
            meta_desc = soup.find("meta", attrs={"name": "description"})
            if not meta_desc:
                findings.append(
                    Finding(
                        plugin_name=self.metadata.name,
                        category=self.metadata.category,
                        target_url=target.url,
                        title="Missing Meta Description Header",
                        severity=Severity.MEDIUM,
                        confidence=1.0,
                        description=(
                            'The page lacks a <meta name="description"> tag. '
                            "Search engines use this to display search snippets."
                        ),
                        remediation=(
                            'Inject a descriptive <meta name="description" content="..."> '
                            "tag inside the <head> section."
                        ),
                        evidence=[],
                    )
                )
            else:
                desc_text = meta_desc.get("content", "").strip()  # type: ignore
                length = len(desc_text)
                if length < 120 or length > 160:
                    findings.append(
                        Finding(
                            plugin_name=self.metadata.name,
                            category=self.metadata.category,
                            target_url=target.url,
                            title="Meta Description Length Out of Optimal Bounds",
                            severity=Severity.LOW,
                            confidence=0.9,
                            description=(
                                f"The meta description length is {length} characters. "
                                "Optimal descriptions range between 120 and 160 characters "
                                "to prevent search engines truncation or inadequate descriptions."
                            ),
                            remediation=(
                                "Modify the meta description length to fall "
                                "between 120 and 160 characters."
                            ),
                            evidence=[
                                Evidence(
                                    type="html_snippet",
                                    data=f"Meta Description ({length} chars): '{desc_text}'",
                                )
                            ],
                        )
                    )

            # 5. Check Headings Hierarchy (h1 tags)
            h1s = soup.find_all("h1")
            h1_count = len(h1s)
            if h1_count == 0:
                findings.append(
                    Finding(
                        plugin_name=self.metadata.name,
                        category=self.metadata.category,
                        target_url=target.url,
                        title="Missing H1 Heading Tag",
                        severity=Severity.MEDIUM,
                        confidence=1.0,
                        description=(
                            "The page lacks an <h1> tag. The <h1> tag serves "
                            "as the primary visual topic indicator."
                        ),
                        remediation=(
                            "Add exactly one <h1> tag representing the "
                            "main title of the page content."
                        ),
                        evidence=[],
                    )
                )
            elif h1_count > 1:
                findings.append(
                    Finding(
                        plugin_name=self.metadata.name,
                        category=self.metadata.category,
                        target_url=target.url,
                        title="Duplicate H1 Headings Detected",
                        severity=Severity.LOW,
                        confidence=1.0,
                        description=(
                            f"Multiple ({h1_count}) <h1> tags were found. "
                            "Using multiple <h1> tags can dilute heading "
                            "importance for indexing algorithms."
                        ),
                        remediation=(
                            "Consolidate page structure so only a single primary heading "
                            "uses the <h1> tag, switching others to <h2> or <h3>."
                        ),
                        evidence=[
                            Evidence(
                                type="html_snippet",
                                data=f"Found <h1> count: {h1_count}",
                            )
                        ],
                    )
                )

            # 6. Check Images Missing Alt Attributes
            images = soup.find_all("img")
            missing_alt_imgs = []
            for img in images:
                alt_val = img.get("alt")
                alt_str = ""
                if isinstance(alt_val, list):
                    alt_str = " ".join(alt_val)
                elif isinstance(alt_val, str):
                    alt_str = alt_val

                if alt_val is None or alt_str.strip() == "":
                    # Store image src as evidence trace
                    src_val = img.get("src", "MISSING_SRC")
                    src_str = "MISSING_SRC"
                    if isinstance(src_val, list):
                        src_str = " ".join(src_val)
                    elif isinstance(src_val, str):
                        src_str = src_val
                    missing_alt_imgs.append(src_str)

            if missing_alt_imgs:
                findings.append(
                    Finding(
                        plugin_name=self.metadata.name,
                        category=self.metadata.category,
                        target_url=target.url,
                        title="Images Missing Alt Attributes",
                        severity=Severity.LOW,
                        confidence=1.0,
                        description=(
                            f"Found {len(missing_alt_imgs)} image(s) lacking descriptive "
                            "'alt' attributes. Alternative text is required for screen-reader "
                            "accessibility and image index SEO matching."
                        ),
                        remediation="Add descriptive 'alt' attributes to all <img> tags.",
                        evidence=[
                            Evidence(
                                type="html_snippet",
                                data=(
                                    "Missing alt image paths: "
                                    f"{', '.join(missing_alt_imgs[:5])}..."
                                ),
                            )
                        ],
                    )
                )

            # 7. Check Canonical Link
            canonical = soup.find("link", attrs={"rel": "canonical"})
            if not canonical:
                findings.append(
                    Finding(
                        plugin_name=self.metadata.name,
                        category=self.metadata.category,
                        target_url=target.url,
                        title="Missing Canonical Link Reference",
                        severity=Severity.LOW,
                        confidence=0.9,
                        description=(
                            'The page is missing a <link rel="canonical"> tag, '
                            "which is essential to prevent duplicate content index issues."
                        ),
                        remediation=(
                            "Add a canonical link tag inside the head pointing "
                            "to the preferred authoritative URL."
                        ),
                        evidence=[],
                    )
                )

        except Exception as e:
            findings.append(
                Finding(
                    plugin_name=self.metadata.name,
                    category=self.metadata.category,
                    target_url=target.url,
                    title="SEO Analyzer Scan Failure",
                    severity=Severity.MEDIUM,
                    confidence=1.0,
                    description=f"SEO Analyzer failed to read or parse target page: {e}",
                    remediation=(
                        "Verify target host is active, online, " "and returning valid HTML content."
                    ),
                    evidence=[Evidence(type="html_snippet", data=str(e))],
                )
            )

        return findings
