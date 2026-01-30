## 2024-05-23 - Prevent Information Leakage in Error Responses
**Vulnerability:** The application was returning raw exception messages in HTTP 500 responses in `autogen_server.py`. This could expose sensitive internal details like stack traces, database schemas, or file paths to attackers.
**Learning:** FastAPI's `HTTPException` detail field is sent directly to the client. Developers often pass the exception string `str(e)` for convenience, not realizing it can contain sensitive info.
**Prevention:** Always catch exceptions, log the full details with `logger.error(..., exc_info=True)`, and raise `HTTPException` with a generic, static error message (e.g., "An internal error occurred").

## 2026-01-19 - Information Leakage in Exception Handling
**Vulnerability:** The application was leaking raw exception messages to clients in `serve_autogen`, `generate_streaming_response`, and `AutogenWorkflow.run`. This exposed internal details like variable names and system errors.
**Learning:** Exception handling blocks were catching `Exception as e` and including `f"{e}"` directly in the `HTTPException` detail or response payload.
**Prevention:** Always sanitize error messages returned to clients. Use generic messages like "An internal error occurred" and log the full exception details server-side with `exc_info=True`.

## 2026-01-16 - Exception Detail Leakage in AutoGen Workflow
**Vulnerability:** The application was catching exceptions and explicitly including `str(e)` in the `HTTPException` detail and `ChatResult` response sent to the client. This exposes internal error details, potential stack trace fragments, or sensitive data contained in exception messages.
**Learning:** Even when catching exceptions, simply passing the exception string to the client is insecure. This was prevalent in both the FastAPI server handlers and the AutoGen workflow logic where error messages were manually constructed.
**Prevention:** Always return generic error messages (e.g., "An internal error occurred") to the client. Log the full exception details server-side using `logger.exception()` or `logger.error(..., exc_info=True)` for debugging.

## 2026-01-20 - Tool Error Information Leakage
**Vulnerability:** The `tool.py` module was catching exceptions in `safe_get_r2r_results`, `safe_get_jira_results` and `async_search`, but was returning the raw exception string (e.g., `f"Error en R2R: {e}"`) to the caller. This meant that the LLM agents (and potentially the end user via the chat interface) received internal error details including IP addresses, usernames, or stack information.
**Learning:** Wrappers labeled `safe_` often only ensure the program doesn't crash, but fail to ensure the *data* returned is safe. Returning `str(e)` in a caught exception block effectively bypasses the benefit of catching the exception from a security perspective.
**Prevention:** Ensure that "safe" wrappers log the full exception details (using `exc_info=True`) but return a static, generic error message to the caller, especially when the caller is an LLM agent or an external user.
