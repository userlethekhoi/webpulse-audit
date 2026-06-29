"""Kaydus CLI color theme — Matrix Hacker Green + White text aesthetic.

Provides ANSI escape sequence constants and helper functions for
consistent terminal styling across all Kaydus output.
"""

import os
import platform
import sys

# ── Base ANSI Codes ────────────────────────────────────────────────────────

RESET = "\033[0m"
BOLD = "\033[1m"
DIM = "\033[2m"
ITALIC = "\033[3m"
UNDERLINE = "\033[4m"
BLINK = "\033[5m"
INVERT = "\033[7m"

# ── Foreground Colors ──────────────────────────────────────────────────────

BLACK = "\033[30m"
RED = "\033[31m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
BLUE = "\033[34m"
MAGENTA = "\033[35m"
CYAN = "\033[36m"
WHITE = "\033[37m"

BRIGHT_BLACK = "\033[90m"
BRIGHT_RED = "\033[91m"
BRIGHT_GREEN = "\033[92m"
BRIGHT_YELLOW = "\033[93m"
BRIGHT_BLUE = "\033[94m"
BRIGHT_MAGENTA = "\033[95m"
BRIGHT_CYAN = "\033[96m"
BRIGHT_WHITE = "\033[97m"

# ── Background Colors ──────────────────────────────────────────────────────

BG_BLACK = "\033[40m"
BG_RED = "\033[41m"
BG_GREEN = "\033[42m"
BG_YELLOW = "\033[43m"
BG_BLUE = "\033[44m"
BG_MAGENTA = "\033[45m"
BG_CYAN = "\033[46m"
BG_WHITE = "\033[47m"

BG_BRIGHT_GREEN = "\033[102m"

# ── Kaydus Brand Colors — Matrix Hacker Theme ──────────────────────────────

# Primary green gradient — used for brand name, banner, prompt
KAYDUS_NEON = "\033[38;5;46m"        # Pure neon green (Matrix code)
KAYDUS_GREEN = "\033[38;5;40m"       # Vibrant hacker green
KAYDUS_DARK_GREEN = "\033[38;5;28m"  # Dark green (banner top)
KAYDUS_DEEP_GREEN = "\033[38;5;22m"  # Deep green (banner base)

# White family — main text, labels, descriptions
TEXT_WHITE = "\033[38;5;255m"        # Soft white (main body text)
TEXT_BRIGHT = "\033[38;5;231m"       # Pure bright white (headings)
TEXT_SILVER = "\033[38;5;250m"       # Silver (dim/secondary text)
TEXT_GRAY = "\033[38;5;242m"         # Gray (subtle hints)

# Accent colors
ACCENT_CYAN = "\033[38;5;51m"        # Cyan accent (URLs, links)
ACCENT_YELLOW = "\033[38;5;226m"     # Warning yellow
ACCENT_MINT = "\033[38;5;49m"        # Mint green (success)

# Severity colors (for findings)
SEV_CRITICAL = "\033[1;38;5;196m"    # Bright red
SEV_HIGH = "\033[1;38;5;208m"        # Orange
SEV_MEDIUM = "\033[1;38;5;226m"      # Yellow
SEV_LOW = "\033[1;38;5;51m"          # Cyan
SEV_INFO = "\033[1;38;5;250m"        # Silver

# ── Helpers ────────────────────────────────────────────────────────────────

_supports_color: bool | None = None


def supports_color() -> bool:
    """Determine if the terminal supports ANSI color output."""
    global _supports_color
    if _supports_color is not None:
        return _supports_color

    if "NO_COLOR" in os.environ:
        _supports_color = False
        return False

    if not sys.stdout.isatty():
        _supports_color = False
        return False

    plat = platform.system()
    if plat == "Windows":
        if sys.stdout.isatty():
            _supports_color = True
            return True
        _supports_color = False
        return False

    _supports_color = True
    return True


def c(text: str, *codes: str) -> str:
    """Wrap text with color codes if terminal supports color."""
    if not supports_color():
        return text
    return "".join(codes) + text + RESET


# ── Style Functions ─────────────────────────────────────────────────────────

def style_critical(t: str) -> str:
    return c(t, SEV_CRITICAL)  # Red — keeps red for danger signals


def style_high(t: str) -> str:
    return c(t, SEV_HIGH)  # Orange


def style_medium(t: str) -> str:
    return c(t, SEV_MEDIUM)  # Yellow


def style_low(t: str) -> str:
    return c(t, SEV_LOW)  # Cyan


def style_info(t: str) -> str:
    return c(t, SEV_INFO)  # Silver


def style_brand(t: str) -> str:
    """Brand name — bold neon green."""
    return c(t, BOLD, KAYDUS_NEON)


def style_accent(t: str) -> str:
    """Accent text — soft white."""
    return c(t, TEXT_WHITE)


def style_dim(t: str) -> str:
    """Dim/secondary text — gray."""
    return c(t, DIM, TEXT_GRAY)


def style_text(t: str) -> str:
    """Main body text — soft white for readability."""
    return c(t, TEXT_WHITE)


def style_heading(t: str) -> str:
    """Section heading — bright white bold."""
    return c(t, BOLD, TEXT_BRIGHT)


def style_error(t: str) -> str:
    """Error messages — bold bright red."""
    return c(t, BOLD, BRIGHT_RED)


def style_success(t: str) -> str:
    """Success messages — bold mint green."""
    return c(t, BOLD, ACCENT_MINT)


def style_warning(t: str) -> str:
    """Warning messages — bold yellow."""
    return c(t, BOLD, ACCENT_YELLOW)


def style_prompt(t: str) -> str:
    """CLI prompt — bold neon green."""
    return c(t, BOLD, KAYDUS_NEON)


def style_url(t: str) -> str:
    """URLs/links — underlined cyan."""
    return c(t, UNDERLINE, ACCENT_CYAN)
