import re
from typing import Any

# Matches control characters except newline (\n), carriage return (\r), and tab (\t)
CONTROL_CHAR_PATTERN = re.compile(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]')


def sanitize_log_input(input_str: Any) -> str:
    """Sanitizes input string for logging to prevent log injection and terminal spoofing.

    Removes control characters (e.g., ANSI escapes, null bytes) and
    escapes newline and carriage return characters.
    """
    if not input_str:
        return ""
    if not isinstance(input_str, str):
        input_str = str(input_str)

    # Remove control characters first
    safe_str = CONTROL_CHAR_PATTERN.sub("", input_str)
    # Then escape newlines and carriage returns
    return safe_str.replace("\n", "\\n").replace("\r", "\\r")
