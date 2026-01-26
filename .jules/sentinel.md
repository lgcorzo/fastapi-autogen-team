


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

## 2025-05-23 - Information Leakage in LLM Tools
**Vulnerability:** Helper functions in `tool.py` (like `safe_get_jira_results`) were catching exceptions and returning the raw error message to the caller (async search), which would then be passed to the LLM or user. This leaked sensitive configuration details like API keys or internal URLs contained in the exception.
**Learning:** It is tempting to return detailed errors to LLM agents to help them "self-correct", but this bypasses security boundaries if the error contains secrets.
**Prevention:** Wrappers around external API calls must sanitize return values on error. Log the full error server-side, but return a generic failure message to the tool consumer.
