"""Kaydus slash-command handlers — delegates to WebPulse engines.

Each handler takes a target URL/domain and optional flags, runs the
appropriate WebPulse scan, and returns formatted output.
"""

from __future__ import annotations

import asyncio
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from kaydus.banner import get_mini_header
from kaydus.theme import (
    style_accent,
    style_brand,
    style_critical,
    style_dim,
    style_error,
    style_high,
    style_info,
    style_low,
    style_medium,
    style_prompt,
    style_success,
    style_text,
    style_warning,
)
from webpulse.core.config import AppConfig, ConfigManager
from webpulse.core.plugin_loader import PluginLoader
from webpulse.reports.reporter import ReportGenerator
from webpulse.reports.schemas import Severity, Target
from webpulse.utils.network import AsyncNetworkClient

# ── Data Classes ────────────────────────────────────────────────────────────


@dataclass
class ScanResult:
    """Container for scan execution results."""

    target_url: str
    duration_seconds: float
    findings: list[Any]
    health_score: float
    risk_score: float
    pages_scanned: int
    errors: list[str]

    @property
    def critical_count(self) -> int:
        return sum(1 for f in self.findings if f.severity == Severity.CRITICAL)

    @property
    def high_count(self) -> int:
        return sum(1 for f in self.findings if f.severity == Severity.HIGH)

    @property
    def medium_count(self) -> int:
        return sum(1 for f in self.findings if f.severity == Severity.MEDIUM)

    @property
    def low_count(self) -> int:
        return sum(1 for f in self.findings if f.severity == Severity.LOW)


# ── Spinner ─────────────────────────────────────────────────────────────────

_SPINNER_FRAMES = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
_SPINNER_SPEED = 0.08


class Spinner:
    """Simple terminal spinner for showing scan progress."""

    def __init__(self, message: str) -> None:
        self.message = message
        self._running = False

    async def spin(self, coro: Any) -> Any:
        """Run the spinner while awaiting a coroutine.

        Args:
            coro: The coroutine to await.

        Returns:
            The result of the coroutine.
        """
        self._running = True
        idx = 0

        task = asyncio.ensure_future(coro)

        while self._running and not task.done():
            frame = _SPINNER_FRAMES[idx % len(_SPINNER_FRAMES)]
            sys.stdout.write(
                f"\r  {style_brand(frame)} {style_text(self.message)}"
            )
            sys.stdout.flush()
            idx += 1
            await asyncio.sleep(_SPINNER_SPEED)

        sys.stdout.write("\r" + " " * (len(self.message) + 10) + "\r")
        sys.stdout.flush()
        self._running = False

        return await task


# ── Core Scan Logic ─────────────────────────────────────────────────────────


async def _run_scan(target_url: str, plugin_filter: list[str] | None = None) -> ScanResult:
    """Execute a focused WebPulse scan on a target URL.

    Args:
        target_url: The target URL or domain to scan.
        plugin_filter: Optional list of plugin names to run (e.g., ['seo']).
                       If None, runs all enabled plugins.

    Returns:
        ScanResult with findings and scores.
    """
    errors: list[str] = []

    # Ensure scheme prefix
    if not (target_url.startswith("http://") or target_url.startswith("https://")):
        target_url = "https://" + target_url

    # Load config
    config_manager = ConfigManager()
    config: AppConfig = config_manager.load_config()

    client = AsyncNetworkClient(
        allow_private_ips=config.network.allow_private_ips,
        user_agent=config.network.user_agent,
        timeout=float(config.core.timeout),
    )
    start_time = time.monotonic()

    try:
        # Discover plugins
        loader = PluginLoader()
        search_paths = [
            Path(__file__).parent.parent / "webpulse" / "modules",
            Path.cwd() / "plugins",
        ]
        plugin_classes = loader.discover_plugins(search_paths)

        active_plugins = []
        for cls in plugin_classes:
            plugin = cls()
            plugin_name = plugin.metadata.name

            # Filter plugins if specified
            if plugin_filter is not None:
                category = plugin.metadata.category
                if category not in plugin_filter:
                    continue

            enabled = True
            mod_conf: dict[str, Any] = {}
            if hasattr(config.modules, plugin_name):
                attr = getattr(config.modules, plugin_name)
                enabled = getattr(attr, "enabled", True)
                if hasattr(attr, "model_dump"):
                    mod_conf = attr.model_dump()

            if enabled:
                await plugin.on_load(mod_conf)
                active_plugins.append(plugin)

        # Execute scan
        target = Target(url=target_url)
        findings: list[Any] = []

        for plugin in active_plugins:
            try:
                pf = await plugin.execute(target, client)
                findings.extend(pf)
            except Exception as e:
                errors.append(f"{plugin.metadata.name}: {e}")

        # Generate scores
        duration = time.monotonic() - start_time
        timestamp = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

        generator = ReportGenerator(
            target_url=target_url,
            scan_timestamp=timestamp,
            duration_seconds=duration,
            findings=findings,
            auth_enabled=False,
            auth_status="DISABLED",
            max_depth=0,
            max_pages=1,
            pages_discovered=1,
            pages_scanned=1,
            scanned_urls=[target_url],
        )

        return ScanResult(
            target_url=target_url,
            duration_seconds=duration,
            findings=findings,
            health_score=generator.scores.get("overall_health_score", 0),
            risk_score=generator.scores.get("risk_score", 0),
            pages_scanned=1,
            errors=errors,
        )

    finally:
        await client.close()


# ── Output Formatters ───────────────────────────────────────────────────────


def _format_findings(result: ScanResult) -> str:
    """Format scan findings into a colorized terminal report.

    Args:
        result: The scan result to format.

    Returns:
        Formatted string with color codes.
    """
    lines: list[str] = []

    # Header
    lines.append(get_mini_header(f"Scan Report: {result.target_url}"))
    lines.append("")

    # Stats row
    health_color = style_critical if result.health_score < 60 else style_warning if result.health_score < 80 else style_success
    risk_color = style_critical if result.risk_score > 7 else style_warning if result.risk_score > 4 else style_success

    lines.append(f"  {style_text('Health Score:')}  {health_color(f'{result.health_score:.0f}%')}")
    lines.append(f"  {style_text('Risk Score:')}    {risk_color(f'{result.risk_score:.1f}/10')}")
    lines.append(f"  {style_text('Duration:')}      {style_accent(f'{result.duration_seconds:.2f}s')}")
    lines.append(f"  {style_text('Findings:')}      {style_critical(str(result.critical_count))} critical  "
                 f"{style_high(str(result.high_count))} high  "
                 f"{style_medium(str(result.medium_count))} medium  "
                 f"{style_low(str(result.low_count))} low")
    lines.append("")

    # Findings details
    if not result.findings:
        lines.append(f"  {style_success('✓ No issues found!')}")
    else:
        for finding in result.findings:
            sev_style = {
                Severity.CRITICAL: style_critical,
                Severity.HIGH: style_high,
                Severity.MEDIUM: style_medium,
                Severity.LOW: style_low,
                Severity.INFO: style_info,
            }.get(finding.severity, style_dim)

            sev_tag = f"[{finding.severity.value}]"
            lines.append(f"  {sev_style(sev_tag)} {style_brand(finding.title)}")
            lines.append(f"  {style_text(finding.description[:120])}...")
            lines.append(f"  {style_accent('→ Fix:')} {style_text(finding.remediation[:100])}")
            lines.append("")

    # Errors
    if result.errors:
        lines.append(get_mini_header("Errors"))
        for err in result.errors:
            lines.append(f"  {style_error('✗')} {style_text(err)}")
        lines.append("")

    return "\n".join(lines)


# ── Slash Command Handlers ──────────────────────────────────────────────────


async def handle_scan(target: str) -> str:
    """Handler for /scan command — full scan with all plugins.

    Args:
        target: The target URL or domain.

    Returns:
        Formatted scan report.
    """
    try:
        result = await _run_scan(target)
        return _format_findings(result)
    except Exception as e:
        return f"\n  {style_error(f'✗ Scan failed: {e}')}\n"


async def handle_seo(target: str) -> str:
    """Handler for /seo command — SEO-only scan.

    Args:
        target: The target URL or domain.

    Returns:
        Formatted SEO report.
    """
    try:
        result = await _run_scan(target, plugin_filter=["seo"])
        return _format_findings(result)
    except Exception as e:
        return f"\n  {style_error(f'✗ SEO scan failed: {e}')}\n"


async def handle_security(target: str) -> str:
    """Handler for /security command — Security-only scan.

    Args:
        target: The target URL or domain.

    Returns:
        Formatted security report.
    """
    try:
        result = await _run_scan(target, plugin_filter=["security"])
        return _format_findings(result)
    except Exception as e:
        return f"\n  {style_error(f'✗ Security scan failed: {e}')}\n"


async def handle_ssl(target: str) -> str:
    """Handler for /ssl command — SSL/TLS-only scan.

    Args:
        target: The target URL or domain.

    Returns:
        Formatted SSL report.
    """
    try:
        result = await _run_scan(target, plugin_filter=["ssl"])
        return _format_findings(result)
    except Exception as e:
        return f"\n  {style_error(f'✗ SSL scan failed: {e}')}\n"


async def handle_http(target: str) -> str:
    """Handler for /http command — HTTP-only scan.

    Args:
        target: The target URL or domain.

    Returns:
        Formatted HTTP report.
    """
    try:
        result = await _run_scan(target, plugin_filter=["http"])
        return _format_findings(result)
    except Exception as e:
        return f"\n  {style_error(f'✗ HTTP scan failed: {e}')}\n"


# ── Command Registry ────────────────────────────────────────────────────────

# Map of slash command → (handler, description, usage)
COMMANDS: dict[str, tuple[Any, str, str]] = {
    "/scan": (handle_scan, "Full website audit — all modules", "/scan <url>"),
    "/seo": (handle_seo, "SEO analysis — titles, meta, headings, images", "/seo <url>"),
    "/security": (handle_security, "Security audit — headers, SQLi, file leaks", "/security <url>"),
    "/ssl": (handle_ssl, "SSL/TLS certificate validation", "/ssl <url>"),
    "/http": (handle_http, "HTTP protocol analysis — compression, HTTP/2", "/http <url>"),
}

NON_SCAN_COMMANDS: dict[str, str] = {
    "/help": "Show this help message",
    "/plugins": "List all loaded plugin modules",
    "/clear": "Clear the terminal screen",
    "/exit": "Exit Kaydus",
    "/quit": "Alias for /exit",
}


def get_help_text() -> str:
    """Render the help message with all available commands.

    Returns:
        Formatted help text.
    """
    lines: list[str] = []
    lines.append(get_mini_header("Kaydus Commands"))
    lines.append("")

    lines.append(f"  {style_brand('SCAN COMMANDS')}")
    lines.append(f"  {style_dim('─' * 50)}")
    for cmd, (_handler, desc, usage) in COMMANDS.items():
        lines.append(f"  {style_prompt(cmd):<14} {style_accent(usage):<30} {style_text(desc)}")
    lines.append("")

    lines.append(f"  {style_brand('GENERAL COMMANDS')}")
    lines.append(f"  {style_dim('─' * 50)}")
    for cmd, desc in NON_SCAN_COMMANDS.items():
        lines.append(f"  {style_prompt(cmd):<14} {style_text(desc)}")
    lines.append("")

    lines.append(f"  {style_accent('Tip: Type a URL directly to run a full scan, or use /command <url> for focused scans.')}")
    lines.append("")

    return "\n".join(lines)
