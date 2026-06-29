"""Kaydus Interactive REPL — Main entry point.

Launches an interactive read-eval-print loop with slash-command dispatching,
readline history, colored prompts, and WebPulse engine integration.
"""

from __future__ import annotations

import asyncio
import os
import re
import sys
from pathlib import Path
from typing import Any

from kaydus.banner import get_banner, get_mini_header, get_system_info_card
from kaydus.commands import COMMANDS, NON_SCAN_COMMANDS, get_help_text
from kaydus.input_handler import live_input
from kaydus.theme import (
    style_brand,
    style_error,
    style_prompt,
    style_success,
    style_text,
    style_warning,
)

# ── Slash Command Completer ─────────────────────────────────────────────────

_ALL_SLASH_COMMANDS = list(COMMANDS.keys()) + list(NON_SCAN_COMMANDS.keys())


def _slash_completer(text: str) -> list[str]:
    """Return matching slash commands sorted by relevance (closest match first).

    Args:
        text: The current input buffer text.

    Returns:
        List of styled suggestion lines, best match first.
    """
    if not text.startswith("/"):
        return []

    # Find matches
    matches = [cmd for cmd in _ALL_SLASH_COMMANDS if cmd.startswith(text)]

    # Build (cmd, desc) pairs
    pairs: list[tuple[str, str]] = []
    for m in matches:
        if m in COMMANDS:
            _, desc, _ = COMMANDS[m]
            pairs.append((m, desc))
        else:
            desc = NON_SCAN_COMMANDS.get(m, "")
            pairs.append((m, desc))

    # Sort: shorter commands first (closest match), then alphabetically
    pairs.sort(key=lambda x: (len(x[0]), x[0]))

    # Format as vertical list — align descriptions
    max_cmd_len = max(len(cmd) for cmd, _ in pairs) if pairs else 0
    lines: list[str] = []
    for cmd, desc in pairs:
        padding = " " * (max_cmd_len - len(cmd) + 2)
        lines.append(f"  {style_prompt(cmd)}{padding}{style_text(desc)}")

    return lines


def _prompt_fn(_text: str) -> str:
    """Build the Kaydus prompt line with optional live buffer.

    Args:
        text: The current input buffer.

    Returns:
        Styled prompt string.
    """
    return f"\n{style_prompt('kaydus')} {style_text('»')} "


# ── Input Helpers ───────────────────────────────────────────────────────────


def _get_input() -> str:
    """Read user input with live slash-command autocomplete using live_input.

    Returns:
        The user's input string, stripped.
    """
    try:
        raw = live_input(_prompt_fn, _slash_completer)
        return raw.strip()
    except (EOFError, KeyboardInterrupt):
        print()
        return "/exit"


# ── URL Detection ───────────────────────────────────────────────────────────


_URL_PATTERN = re.compile(
    r"^(?:https?://)?[\w.-]+\.[a-z]{2,}(?:[/?#][^\s]*)?$", re.IGNORECASE
)


def _is_url(text: str) -> bool:
    """Check if the input text looks like a URL or domain name.

    Args:
        text: Input text to check.

    Returns:
        True if the text matches URL/domain patterns.
    """
    if text.startswith("/"):
        return False
    return bool(_URL_PATTERN.match(text))


# ── Command Dispatch ────────────────────────────────────────────────────────


async def _dispatch(raw_input: str) -> None:
    """Parse and dispatch user input to the appropriate handler.

    Supports:
      - /command <args>  → slash commands
      - <url>            → auto-runs full /scan
      - anything else    → error message

    Args:
        raw_input: The raw user input string.
    """
    if not raw_input:
        return

    parts = raw_input.split(maxsplit=1)
    cmd = parts[0].lower()
    args = parts[1] if len(parts) > 1 else ""

    # ── General Commands ────────────────────────────────────────────────
    if cmd in ("/exit", "/quit", "exit", "quit"):
        print(
            f"\n  {style_success('✓')} {style_text('Kaydus signing off. Stay secure.')}\n"
        )
        sys.exit(0)

    if cmd == "/clear":
        os.system("cls" if os.name == "nt" else "clear")
        print(get_banner())
        return

    if cmd == "/help":
        print(get_help_text())
        return

    if cmd == "/plugins":
        _show_plugins()
        return

    # ── Scan Commands ───────────────────────────────────────────────────
    if cmd in COMMANDS:
        if not args:
            print(
                f"\n  {style_warning('⚠')}  {style_text(f'Usage: {cmd} <url>')}"
            )
            print(f"  {style_text('Example: ' + cmd + ' example.com')}")
            return

        handler, _desc, _usage = COMMANDS[cmd]
        print(
            f"\n  {style_brand('⚡')} {style_text('Running')} "
            f"{style_prompt(cmd)} {style_text('on ' + args + '...')}"
        )
        await _run_with_spinner(handler, args)
        return

    # ── Auto-detect URL → full scan ─────────────────────────────────────
    if _is_url(raw_input):
        print(
            f"\n  {style_brand('⚡')} {style_text('Full scan on')} "
            f"{style_prompt(raw_input)}..."
        )
        handler, _desc, _usage = COMMANDS["/scan"]
        await _run_with_spinner(handler, raw_input)
        return

    # ── Unknown command ─────────────────────────────────────────────────
    msg = "\n  " + style_error("✗") + "  " + style_text("Unknown command: '" + cmd + "'")
    print(msg)
    print(
        f"  {style_text('Type')} {style_prompt('/help')} "
        f"{style_text('to see available commands.')}"
    )


async def _run_with_spinner(handler: Any, target: str) -> None:
    """Run a handler with a spinning progress indicator.

    Args:
        handler: The async handler function.
        target: The target URL/domain argument.
    """
    frames = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]

    async def spin_and_run() -> str:
        result = await handler(target)
        return str(result)

    task = asyncio.ensure_future(spin_and_run())
    idx = 0

    while not task.done():
        frame = frames[idx % len(frames)]
        sys.stdout.write(f"\r  {style_prompt(frame)} {style_text('Scanning...')}")
        sys.stdout.flush()
        idx += 1
        await asyncio.sleep(0.08)

    sys.stdout.write("\r" + " " * 30 + "\r")
    sys.stdout.flush()

    try:
        result = await task
        print(result)
    except Exception as e:
        print(f"\n  {style_error('✗ Error: ' + str(e))}")


# ── Plugin Listing ──────────────────────────────────────────────────────────


def _show_plugins() -> None:
    """Display all loaded WebPulse plugin modules."""
    try:
        from webpulse.core.plugin_loader import PluginLoader

        loader = PluginLoader()
        search_paths: list[Path] = [
            Path(__file__).parent.parent / "webpulse" / "modules",
            Path.cwd() / "plugins",
        ]
        classes = loader.discover_plugins(search_paths)

        print(get_mini_header("Loaded Plugins"))
        for cls in classes:
            p = cls()
            print(f"  {style_prompt('▸')} {style_brand(p.metadata.name)}")
            print(
                f"    {style_text('Category:')} {p.metadata.category}  "
                f"{style_text('Version:')} {p.metadata.version}"
            )
    except Exception as e:
        print(f"\n  {style_error('✗ Failed to load plugins: ' + str(e))}")


# ── Main Entrypoint ─────────────────────────────────────────────────────────


def main() -> None:
    """Launch the Kaydus interactive audit CLI."""
    # Print splash banner
    print(get_banner())

    # Print system information card
    print(get_system_info_card())
    print()

    # Quick start hint
    print(
        f"  {style_text('Type')} {style_prompt('/help')} "
        f"{style_text('for commands, or paste a URL to scan.')}"
    )
    print(f"  {style_text('Type')} {style_prompt('/exit')} {style_text('to quit.')}")
    print()

    # REPL loop
    while True:
        try:
            raw_input = _get_input()
            asyncio.run(_dispatch(raw_input))
        except KeyboardInterrupt:
            print(
                f"\n  {style_warning('⚠')}  "
                f"{style_text('Press Ctrl+C again or type /exit to quit.')}"
            )
        except Exception as e:
            print(f"\n  {style_error('✗ Unexpected error: ' + str(e))}")


if __name__ == "__main__":
    main()
