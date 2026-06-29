"""Kaydus CLI splash banner — Matrix Hacker Green aesthetic."""

from kaydus.theme import (
    BG_GREEN,
    BOLD,
    KAYDUS_DARK_GREEN,
    KAYDUS_DEEP_GREEN,
    KAYDUS_GREEN,
    KAYDUS_NEON,
    RESET,
    TEXT_BRIGHT,
    TEXT_GRAY,
    TEXT_WHITE,
    supports_color,
)

BANNER = r"""
   ██╗  ██╗ █████╗ ██╗   ██╗██████╗ ██╗   ██╗███████╗
   ██║ ██╔╝ ██╔══██╗╚██╗ ██╔╝██╔══██╗██║   ██║██╔════╝
   █████╔╝  ███████║ ╚████╔╝ ██║  ██║██║   ██║███████╗
   ██╔═██╗  ██╔══██║  ╚██╔╝  ██║  ██║██║   ██║╚════██║
   ██║  ██╗ ██║  ██║   ██║   ██████╔╝╚██████╔╝███████║
   ╚═╝  ╚═╝ ╚═╝  ╚═╝   ╚═╝   ╚═════╝  ╚═════╝ ╚══════╝
"""

TAGLINE = "▸ Advanced Web Security Audit Agent — Powered by WebPulse"


def get_banner() -> str:
    """Render the Kaydus splash banner with green gradient.

    Returns:
        Colorized ASCII art banner string.
    """
    if not supports_color():
        return f"{BANNER}\n{TAGLINE}\n"

    lines = BANNER.strip("\n").split("\n")
    # Gradient: deep green (top) → neon green (bottom)
    colors = [
        KAYDUS_DEEP_GREEN,
        KAYDUS_DARK_GREEN,
        KAYDUS_DARK_GREEN,
        KAYDUS_GREEN,
        KAYDUS_NEON,
        KAYDUS_NEON,
    ]
    colored_lines = []
    for line, color in zip(lines, colors, strict=False):
        colored_lines.append(f"  {color}{line}{RESET}")

    banner_text = "\n".join(colored_lines)
    tagline = f"  {TEXT_GRAY}{TAGLINE}{RESET}"

    return f"\n{banner_text}\n{tagline}\n"


def get_mini_header(title: str) -> str:
    """Render a section header with green accent bar.

    Args:
        title: The section title.

    Returns:
        Colorized section header string.
    """
    if not supports_color():
        return f"\n── {title} ──\n"

    bar = f"{BOLD}{BG_GREEN}{KAYDUS_NEON} {RESET}"
    text = f" {BOLD}{TEXT_BRIGHT}{title}{RESET} "
    return f"\n{bar}{text}\n"


def get_status_line(message: str, status: str = "OK") -> str:
    """Render a status line with a colored status indicator.

    Args:
        message: The status message.
        status: Status label (OK, FAIL, WARN, etc.).

    Returns:
        Colorized status line.
    """
    if not supports_color():
        return f"  [{status}] {message}"

    status_colors = {
        "OK": f"{KAYDUS_NEON}✓{RESET}",
        "FAIL": f"{BRIGHT_RED}✗{RESET}",
        "WARN": f"{ACCENT_YELLOW}⚠{RESET}",
        "→": f"{KAYDUS_NEON}→{RESET}",
    }
    indicator = status_colors.get(status, f"[{status}]")
    return f"  {indicator} {TEXT_WHITE}{message}{RESET}"


def get_system_info_card() -> str:
    """Render a colorized system information card.

    Returns:
        Formatted system information box string.
    """
    from kaydus.system_info import get_sys_info
    from kaydus.theme import (
        style_brand,
        style_text,
        style_accent,
        style_success,
        style_error,
    )

    info = get_sys_info()

    # Truncate values to fit columns
    os_val = info["os"][:18]
    cpu_val = info["cpu"][:22]
    auth_val = info["auth"]

    # Styled Auth
    if auth_val == "ENABLED":
        auth_styled = style_success("ENABLED")
    else:
        auth_styled = style_error("DISABLED")

    if not supports_color():
        return (
            f"  ┌──────────────────────────────────────────────────────────────────────────┐\n"
            f"  │  KAYDUS CLI SYSTEM AUDIT AGENT                                           │\n"
            f"  ├──────────────────────────────────────────────────────────────────────────┤\n"
            f"  │  OS: {os_val:<18} │ CPU: {cpu_val:<22} │ Auth: {auth_val:<8}     │\n"
            f"  └──────────────────────────────────────────────────────────────────────────┘"
        )

    border_top = "  ┌" + "─" * 74 + "┐"
    border_mid = "  ├" + "─" * 74 + "┤"
    border_bottom = "  └" + "─" * 74 + "┘"

    title_line = f"  │  {style_brand('KAYDUS CLI SYSTEM AUDIT AGENT')}{' ' * 43}│"

    os_label = style_text("OS:")
    cpu_label = style_text("CPU:")
    auth_label = style_text("Auth:")

    info_line = (
        f"  │  {os_label} {style_accent(f'{os_val:<18}')} │ "
        f"{cpu_label} {style_accent(f'{cpu_val:<22}')} │ "
        f"{auth_label} {auth_styled:<8}   │"
    )

    return "\n".join([border_top, title_line, border_mid, info_line, border_bottom])


# Re-export for convenience
from kaydus.theme import ACCENT_YELLOW, BRIGHT_RED  # noqa: E402

