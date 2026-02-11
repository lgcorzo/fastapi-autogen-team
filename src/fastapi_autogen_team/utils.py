def sanitize_log_input(input_str: str | None) -> str:
    """Sanitizes input string for logging to prevent log injection.

    Escapes newline and carriage return characters.
    """
    if input_str is None:
        return ""
    return input_str.replace("\n", "\\n").replace("\r", "\\r")
