## 2025-05-20 - Exception Leakage in FastAPI Endpoints
**Vulnerability:** API endpoints were catching exceptions and including the raw exception message in the `HTTPException` detail, potentially exposing sensitive information (secrets, stack traces, internal paths) to the client.
**Learning:** Default exception handling patterns that blindly forward `str(e)` to the client are a common source of information leakage. Developers often do this for debugging convenience without realizing the security implication.
**Prevention:** Always catch exceptions and log the full details (including stack trace) server-side, but return a generic, sanitized error message to the client. Use a consistent error handling utility or middleware if possible.
