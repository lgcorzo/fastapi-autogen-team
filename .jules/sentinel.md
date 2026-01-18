## 2025-05-23 - [Prevent Exception Leakage in API Responses]
**Vulnerability:** The API endpoints in `autogen_server.py` were catching generic `Exception` and including the exception message `e` directly in the `HTTPException` detail. This could potentially leak sensitive information (stack traces, internal paths, database connection strings, etc.) to the client.
**Learning:** Even when logging errors server-side, it is crucial to sanitize the error message returned to the client. Developers often include `{e}` in the response for easier debugging, but this is a security risk in production.
**Prevention:** Always use generic error messages (e.g., "An internal error occurred") in client-facing responses for 500 errors. Log the full exception details server-side for debugging.
