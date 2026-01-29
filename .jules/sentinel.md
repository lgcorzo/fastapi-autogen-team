


## 2024-05-23 - Prevent Information Leakage in Error Responses
**Vulnerability:** The application was returning raw exception messages in HTTP 500 responses in `autogen_server.py`. This could expose sensitive internal details like stack traces, database schemas, or file paths to attackers.
**Learning:** FastAPI's `HTTPException` detail field is sent directly to the client. Developers often pass the exception string `str(e)` for convenience, not realizing it can contain sensitive info.
**Prevention:** Always catch exceptions, log the full details with `logger.error(..., exc_info=True)`, and raise `HTTPException` with a generic, static error message (e.g., "An internal error occurred").

## 2026-01-19 - Information Leakage in Exception Handling
**Vulnerability:** The application was leaking raw exception messages to clients in `serve_autogen`, `generate_streaming_response`, and `AutogenWorkflow.run`. This exposed internal details like variable names and system errors.
**Learning:** Exception handling blocks were catching `Exception as e` and including `f"{e}"` directly in the `HTTPException` detail or response payload.
**Prevention:** Always sanitize error messages returned to clients. Use generic messages like "An internal error occurred" and log the full exception details server-side with `exc_info=True`.

=======
## 2024-05-22 - Exception Handling Information Leakage
**Vulnerability:** The application was leaking sensitive internal exception details (including potential secrets or stack traces) to API clients via `HTTPException(detail=f"{e}")` and in streaming response payloads.
**Learning:** Developers often pass `str(e)` to error responses to help with debugging, but this exposes internal state, paths, and potentially secrets to the user.
**Prevention:** Catch exceptions, log the full details (including stack traces) using `logger.error(..., exc_info=True)`, but return a generic, sanitized message to the client (e.g., "An internal error occurred").
>>>>>>> origin/sentinel/fix-exception-leakage-4082017526931851893
=======
## 2026-01-16 - Exception Detail Leakage in AutoGen Workflow
**Vulnerability:** The application was catching exceptions and explicitly including `str(e)` in the `HTTPException` detail and `ChatResult` response sent to the client. This exposes internal error details, potential stack trace fragments, or sensitive data contained in exception messages.
**Learning:** Even when catching exceptions, simply passing the exception string to the client is insecure. This was prevalent in both the FastAPI server handlers and the AutoGen workflow logic where error messages were manually constructed.
**Prevention:** Always return generic error messages (e.g., "An internal error occurred") to the client. Log the full exception details server-side using `logger.exception()` or `logger.error(..., exc_info=True)` for debugging.
>>>>>>> origin/sentinel/fix-exception-leakage-9932621092945243215

## 2026-01-29 - Exception Leakage in Tool Results
**Vulnerability:** The functions `safe_get_r2r_results` and `safe_get_jira_results` in `tool.py` were catching exceptions but returning the raw exception message string to the caller. This could leak internal error details, credentials, or stack traces to the LLM agent or end user.
**Learning:** While the functions were named "safe", they were only safe from crashing the application, not safe from information leakage. Developers might assume catching an exception is enough, but how the exception is reported matters.
**Prevention:** In "safe" wrappers, catch exceptions, log them with full details (`exc_info=True`) for debugging, but always return a generic, sanitized error message to the caller.
