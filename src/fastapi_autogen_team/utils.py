from typing import Any

def sanitize_log_input(input_str: Any) -> str:
    """
    Sanitizes user input to prevent log injection attacks.
    Escapes newline and carriage return characters.
    """
    if not isinstance(input_str, str):
        return str(input_str)
    return input_str.replace("\n", "\\n").replace("\r", "\\r")
