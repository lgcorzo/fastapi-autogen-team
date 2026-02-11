from typing import Any


def sanitize_log_input(input_str: Any) -> str:
    """Sanitizes input string for logging to prevent log injection.

    Escapes newline and carriage return characters.
    """
    if not input_str:
        return ""
    if not isinstance(input_str, str):
        input_str = str(input_str)

    safe_str: str = input_str
    return safe_str.replace("\n", "\\n").replace("\r", "\\r")
