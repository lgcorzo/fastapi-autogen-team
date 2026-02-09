def sanitize_log_input(input_str: str) -> str:
    """Sanitizes input string for logging by escaping newlines and carriage returns.

    This prevents log injection attacks where an attacker can forge log entries.

    Args:
        input_str: The input string to sanitize.

    Returns:
        The sanitized string with newlines and carriage returns escaped.
    """
    if not input_str:
        return ""
    return input_str.replace("\n", "\\n").replace("\r", "\\r")
