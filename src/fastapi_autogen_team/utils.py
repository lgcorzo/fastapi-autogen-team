from typing import Optional


def sanitize_log_input(input_str: Optional[str]) -> str:
    """Sanitizes input string for logging to prevent log injection.

    Replaces newlines and carriage returns with escaped versions.
    """
    if not input_str:
        return ""
    return input_str.replace("\n", "\\n").replace("\r", "\\r")
