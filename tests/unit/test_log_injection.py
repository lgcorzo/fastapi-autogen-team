from fastapi_autogen_team.utils import sanitize_log_input

def test_sanitize_log_input_normal_string():
    """Test sanitization of a normal string."""
    input_str = "This is a normal string."
    assert sanitize_log_input(input_str) == "This is a normal string."

def test_sanitize_log_input_with_newlines():
    """Test sanitization of a string with newlines."""
    input_str = "Line 1\nLine 2"
    assert sanitize_log_input(input_str) == "Line 1\\nLine 2"

def test_sanitize_log_input_with_carriage_returns():
    """Test sanitization of a string with carriage returns."""
    input_str = "Line 1\rLine 2"
    assert sanitize_log_input(input_str) == "Line 1\\rLine 2"

def test_sanitize_log_input_with_mixed_newlines():
    """Test sanitization of a string with mixed newlines."""
    input_str = "Line 1\r\nLine 2"
    assert sanitize_log_input(input_str) == "Line 1\\r\\nLine 2"

def test_sanitize_log_input_none():
    """Test sanitization of None."""
    assert sanitize_log_input(None) == "None"

def test_sanitize_log_input_empty_string():
    """Test sanitization of an empty string."""
    assert sanitize_log_input("") == ""
