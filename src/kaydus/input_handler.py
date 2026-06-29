"""Character-by-character input handler with live slash-command autosuggestions.

Reads keystrokes one at a time (via msvcrt on Windows, termios on Unix),
displays real-time command suggestions below the input line as the user types.
"""

import sys
import re
from collections.abc import Callable

# ── Platform-specific character reader ──────────────────────────────────────

if sys.platform == "win32":
    import msvcrt

    def _getch() -> str:
        """Read a single character from stdin (Windows)."""
        ch = msvcrt.getwch()
        # Handle special keys
        if ch == "\r":
            return "\n"
        if ch == "\x08":
            return "\b"
        if ch == "\t":
            return "\t"
        if ch in ("\x00", "\xe0"):
            # Extended key prefix — read next byte and ignore
            msvcrt.getwch()
            return ""
        return ch

else:
    import termios
    import tty

    def _getch() -> str:
        """Read a single character from stdin (Unix)."""
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setraw(fd)
            ch = sys.stdin.read(1)
            if ch == "\x1b":
                # Escape sequence — read next 2 bytes
                ch2 = sys.stdin.read(1)
                ch3 = sys.stdin.read(1)
                if ch2 == "[":
                    if ch3 == "A":
                        return "UP"
                    if ch3 == "B":
                        return "DOWN"
                    if ch3 == "C":
                        return "RIGHT"
                    if ch3 == "D":
                        return "LEFT"
                    if ch3 == "3":
                        sys.stdin.read(1)  # consume ~
                        return "DELETE"
                return ""
            if ch == "\x7f":
                return "\b"
            if ch == "\r":
                return "\n"
            return ch
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)


# ── Live Autocomplete Input ─────────────────────────────────────────────────


def live_input(
    prompt_fn: Callable[[str], str],
    completer_fn: Callable[[str], list[str]],
) -> str:
    """Read a line of input with live autocomplete suggestions shown above the prompt.

    As the user types, matching completions appear in a box above the prompt
    without triggering terminal scrolling or causing cursor desync issues.

    Args:
        prompt_fn: Function that takes the current buffer and returns a styled prompt string.
        completer_fn: Function that takes the current buffer and returns matching completions.

    Returns:
        The user's full input string (without the suggestion line).
    """
    buffer: list[str] = []
    cursor_pos: int = 0
    suggestion_count: int = 0  # Number of suggestion lines currently displayed (including borders)

    def _refresh() -> None:
        """Redraw the input line with prompt, buffer, and live suggestions above."""
        nonlocal suggestion_count

        text = "".join(buffer)
        prompt = prompt_fn(text)

        # Compute suggestions
        matches = completer_fn(text)
        new_suggestions = matches if (matches and text.startswith("/")) else []

        # 1. Clear old suggestion lines (above the input line)
        if suggestion_count > 0:
            sys.stdout.write(f"\033[{suggestion_count}A")
            for _ in range(suggestion_count):
                sys.stdout.write("\r\033[K\033[B")

        # 2. Draw new suggestion box if there are suggestions
        if new_suggestions:
            suggestion_count = len(new_suggestions) + 2
            sys.stdout.write(f"\033[{suggestion_count}A")

            # Draw top border
            sys.stdout.write("\r\033[K┌── Gợi ý lệnh ─────────────────────────────────────────────────────┐\033[B")

            for line in new_suggestions:
                # Strip ANSI escapes to compute actual length
                clean_line = re.sub(r"\033\[[0-9;]*m", "", line)
                content_len = len(clean_line)
                # Suggestion box width is 70 chars inside borders (72 total)
                padding = " " * max(0, 68 - content_len)
                sys.stdout.write(f"\r\033[K│ {line}{padding} │\033[B")

            # Draw bottom border
            sys.stdout.write("\r\033[K└───────────────────────────────────────────────────────────────────┘\033[B")
        else:
            suggestion_count = 0

        # 3. Clear and draw the current input line
        sys.stdout.write("\r\033[K")
        sys.stdout.write(prompt + text)

        # 4. Move cursor to correct position inside the text buffer
        if cursor_pos < len(buffer):
            sys.stdout.write(f"\033[{len(buffer) - cursor_pos}D")

        sys.stdout.flush()

    _refresh()

    while True:
        ch = _getch()
        if not ch:
            continue

        if ch == "\n":
            # Clear all suggestion lines (above the input line)
            if suggestion_count > 0:
                sys.stdout.write(f"\033[{suggestion_count}A")
                for _ in range(suggestion_count):
                    sys.stdout.write("\r\033[K\033[B")
            sys.stdout.write("\n")
            sys.stdout.flush()
            return "".join(buffer)

        if ch in ("\b", "\x7f"):
            if cursor_pos > 0:
                buffer.pop(cursor_pos - 1)
                cursor_pos -= 1

        elif ch == "DELETE":
            if cursor_pos < len(buffer):
                buffer.pop(cursor_pos)

        elif ch == "LEFT":
            if cursor_pos > 0:
                cursor_pos -= 1

        elif ch == "RIGHT":
            if cursor_pos < len(buffer):
                cursor_pos += 1

        elif ch == "\t":
            # Tab: auto-complete with first match
            text = "".join(buffer)
            matches = completer_fn(text)
            if matches and text.startswith("/"):
                # Find common prefix
                common = matches[0]
                # Extract command from styled line representation
                # matches[0] looks like: "  /scan  Full website audit"
                # Let's clean and extract just the command word
                clean_match = re.sub(r"\033\[[0-9;]*m", "", common).strip()
                cmd_word = clean_match.split()[0] if clean_match else ""
                
                if cmd_word.startswith(text):
                    # Replace buffer with the completed command word
                    buffer = list(cmd_word)
                    cursor_pos = len(buffer)

        elif len(ch) == 1 and ord(ch) >= 32:
            # Printable character
            buffer.insert(cursor_pos, ch)
            cursor_pos += 1

        _refresh()

