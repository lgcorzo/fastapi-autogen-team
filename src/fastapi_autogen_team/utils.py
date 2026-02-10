
def sanitize_log_input(input_str: str | None) -> str:
    """Sanitizes input for logging to prevent log injection."""
    if input_str is None:
        return "None"
    return input_str.replace("\n", "\\n").replace("\r", "\\r")
