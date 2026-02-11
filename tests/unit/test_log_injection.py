import pytest
from fastapi_autogen_team.utils import sanitize_log_input

def test_sanitize_log_input_normal():
    assert sanitize_log_input("hello") == "hello"

def test_sanitize_log_input_newlines():
    assert sanitize_log_input("hello\nworld") == "hello\\nworld"

def test_sanitize_log_input_carriage_returns():
    assert sanitize_log_input("hello\rworld") == "hello\\rworld"

def test_sanitize_log_input_mixed():
    assert sanitize_log_input("hello\r\nworld") == "hello\\r\\nworld"

def test_sanitize_log_input_none():
    assert sanitize_log_input(None) == "None"

def test_sanitize_log_input_empty():
    assert sanitize_log_input("") == ""
