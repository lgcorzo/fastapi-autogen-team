## 2024-05-23 - Prevent Information Leakage in Error Responses

**Vulnerability:** The application was returning raw exception messages in HTTP 500 responses in `autogen_server.py`. This could expose sensitive internal details like stack traces, database schemas, or file paths to attackers.
**Learning:** FastAPI's `HTTPException` detail field is sent directly to the client. Developers often pass the exception string `str(e)` for convenience, not realizing it can contain sensitive info.
**Prevention:** Always catch exceptions, log the full details with `logger.error(..., exc_info=True)`, and raise `HTTPException` with a generic, static error message (e.g., "An internal error occurred").

## 2026-01-19 - Information Leakage in Exception Handling

**Vulnerability:** The application was leaking raw exception messages to clients in `serve_autogen`, `generate_streaming_response`, and `AutogenWorkflow.run`. This exposed internal details like variable names and system errors.
**Learning:** Exception handling blocks were catching `Exception as e` and including `f"{e}"` directly in the `HTTPException` detail or response payload.
**Prevention:** Always sanitize error messages returned to clients. Use generic messages like "An internal error occurred" and log the full exception details server-side with `exc_info=True`.

## 2024-05-22 - Exception Handling Information Leakage

**Vulnerability:** The application was leaking sensitive internal exception details (including potential secrets or stack traces) to API clients via `HTTPException(detail=f"{e}")` and in streaming response payloads.
**Learning:** Developers often pass `str(e)` to error responses to help with debugging, but this exposes internal state, paths, and potentially secrets to the user.
**Prevention:** Catch exceptions, log the full details (including stack traces) using `logger.error(..., exc_info=True)`, but return a generic, sanitized message to the client (e.g., "An internal error occurred").

## 2026-01-16 - Exception Detail Leakage in AutoGen Workflow

**Vulnerability:** The application was catching exceptions and explicitly including `str(e)` in the `HTTPException` detail and `ChatResult` response sent to the client. This exposes internal error details, potential stack trace fragments, or sensitive data contained in exception messages.
**Learning:** Even when catching exceptions, simply passing the exception string to the client is insecure. This was prevalent in both the FastAPI server handlers and the AutoGen workflow logic where error messages were manually constructed.
**Prevention:** Always return generic error messages (e.g., "An internal error occurred") to the client. Log the full exception details server-side using `logger.exception()` or `logger.error(..., exc_info=True)` for debugging.

## 2026-01-20 - Exception Leakage in handle_response

**Vulnerability:** The `handle_response` function in `autogen_server.py` was raising `HTTPException` with details that included the raw string response or the type of the object. This leaked sensitive data or internal implementation details to the client.
**Learning:** Even helper functions used for response processing can be a source of information leakage if they bubble up raw data in exception details.
**Prevention:** Catch invalid states and log the specific error details (including the raw data) to the server logs, but raise an `HTTPException` with a generic, sanitized message to the client.

## 2026-02-13 - Prevent Prompt Injection via Structural Delimiters

**Vulnerability:** User input could contain sequences like `\n},\n` that mimic the structural delimiters used to build the LLM prompt. This allowed attackers to inject fake prompt blocks (e.g., overriding system instructions).
**Learning:** When constructing prompts by concatenating user input with structural markers, the user input must be sanitized to ensure it cannot reproduce those markers.
**Prevention:** Sanitize all user input used in prompts by altering or escaping sequences that match the prompt's structural delimiters (e.g., replacing `\n},\n` with `\n} ,\n`).

## 2026-02-06 - Log Injection Vulnerability

**Vulnerability:** User-controlled input (like `user` ID, model names, and search `query`) was logged directly, allowing attackers to inject fake log entries via control characters like newlines (`\n`) and carriage returns (`\r`).
**Learning:** Logging raw user input is a security risk (CWE-117). Attackers can spoof log entries to mask malicious activity or confuse log analyzers.
**Prevention:** Always sanitize user input before logging. Use the `sanitize_log_input` helper function to escape control characters.

## 2026-02-13 - Fix CRLF Prompt Injection Bypass

**Vulnerability:** The `sanitize_for_prompt` function relied on exact string matching for `\n},\n` to prevent prompt injection. Attackers could bypass this using CRLF line endings (`\r\n},\r\n`), which the sanitizer failed to detect but the downstream LLM/parser treated as valid delimiters.
**Learning:** Security sanitization logic that relies on exact string matching for structural delimiters is fragile. Variations in whitespace (like CRLF vs LF) can easily bypass such checks.
**Prevention:** Normalize input (e.g., convert all line endings to `\n`) before applying sanitization rules, or use more robust matching (e.g., regex) that accounts for whitespace variations.

## 2026-05-23 - Prevent Dropping of System Messages

**Vulnerability:** The `normalize_input_messages` function in `autogen_server.py` was filtering out system messages from the input, causing any security constraints or instructions in the system prompt to be ignored.
**Learning:** Logic errors in message processing can inadvertently bypass security controls. In this case, a list comprehension intended to process messages was incorrectly filtering them out.
**Prevention:** Ensure that message processing logic correctly handles all message roles, especially system messages which often contain critical security instructions. Verify with unit tests that system messages are preserved.

## 2026-02-17 - Header Injection Vulnerability via User ID

**Vulnerability:** The application read the `x-openwebui-user-id` header and assigned it directly to the internal user model without sanitization. This allowed attackers to inject CRLF characters (`\r\n`) into the User ID, potentially leading to HTTP response splitting or log injection downstream.
**Learning:** Trusting HTTP headers as "safe" input is a common mistake. Any input from the client, including headers, must be treated as untrusted and sanitized.
**Prevention:** Sanitize all header values before using them in internal logic or logging. In this case, `sanitize_log_input` was applied to escape control characters.

## 2024-10-25 - Prevent User ID Injection via Input Sanitization

**Vulnerability:** The application was vulnerable to injection attacks because the `user` ID from the `x-openwebui-user-id` header was passed unsanitized to downstream services (`serve_autogen`, `AutogenWorkflow`). This could lead to Header Injection or Log Injection if the downstream services used this value in sensitive contexts.
**Learning:** Even if input is sanitized for _logging_ locally, the _original_ raw input object might still be passed to other parts of the system.
**Prevention:** Sanitize input fields (like `user` and `model`) _in place_ on the input object before passing it to any service or logging function.
