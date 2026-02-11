def sanitize_log_input(input_str: str | None) -> str:
    """Sanitizes user input for logging to prevent log injection.

    Args:
        input_str: The input string to sanitize.

    Returns:
        The sanitized string with newlines and carriage returns escaped.
        If input_str is None, returns "None".
    """
    if input_str is None:
        return "None"

    return input_str.replace("\n", "\\n").replace("\r", "\\r")
