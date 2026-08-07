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

## 2026-02-14 - Header Injection via User ID

**Vulnerability:** The application was using the `user` ID input directly in HTTP headers (via `create_llm_config`), allowing attackers to inject arbitrary headers (CRLF injection) via newlines.
**Learning:** User inputs used in system configurations or downstream API calls (like HTTP headers) must be sanitized, not just for logging or display.
**Prevention:** Sanitize the `user` ID using `sanitize_log_input` (or similar) to escape control characters before passing it to `AutogenWorkflow` or any downstream service.

## 2026-02-19 - DoS Risk via Unbounded Input

**Vulnerability:** The application accepted unbounded string inputs for `messages`, `model`, and `user` fields in the API payload. This exposed the system to Denial of Service (DoS) attacks via memory exhaustion or excessive processing by sending massive payloads (e.g., 10MB strings).
**Learning:** Relying on default Pydantic validation is insufficient for security; explicit length limits (`max_length`) must be defined for all string inputs, especially those processed by expensive downstream services like LLMs.
**Prevention:** Use Pydantic's `Field(max_length=...)` to strictly enforce reasonable limits on all user-controlled string inputs. For complex types like `Union` in Pydantic V2, use `Annotated` to apply constraints.

## 2024-03-06 - Missing API Security Headers

**Vulnerability:** The application was not setting basic HTTP security headers (`X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`) on API responses. This could allow attackers to perform MIME-sniffing attacks or embed the application in malicious iframes (Clickjacking).
**Learning:** Security headers should be applied globally to all endpoints by default, rather than relying on individual route configurations or reverse proxies, as an added layer of defense.
**Prevention:** Implemented a global FastAPI middleware (`@app.middleware("http")`) to automatically inject `X-Content-Type-Options: nosniff` and `X-Frame-Options: DENY` headers into all `Response` objects before they are returned to the client.

## 2026-03-21 - DoS Risk via Unbounded Input List

**Vulnerability:** The application mitigated string-based DoS risks but missed limiting the length of nested lists (e.g., `content: List[Union[ContentText, ContentImage]]`), leaving a vector for DoS via massive arrays.
**Learning:** Pydantic validation bypasses list length limits unless explicitly constrained, even if inner elements are bounded. Attackers can still exhaust memory by sending enormous arrays of small, valid items.
**Prevention:** Always set `max_length` explicitly on `List` types (using `Annotated` in Pydantic V2) for user-provided data, especially inside nested objects or unions.

## 2026-03-24 - CORS Middleware Empty Origins Misconfiguration

**Vulnerability:** The application was parsing `ALLOWED_ORIGINS` by splitting an empty string, which resulted in a list containing an empty string `[""]`. This was passed directly to FastAPI's `CORSMiddleware`, enabling broken CORS configurations or failing pre-flight OPTIONS requests (e.g., throwing an exception when `allow_credentials=True` is combined with a wildcard or malformed origin).
**Learning:** Default fallback values for list-based environment variables like CORS origins must be rigorously validated. A default empty string split by comma creates an invalid list of one empty string, not an empty list.
**Prevention:** Always strip whitespace and filter out empty strings when parsing comma-separated environment variables (e.g., `[origin.strip() for origin in os.getenv("ALLOWED_ORIGINS", "").split(",") if origin.strip()]`). Conditionally add the `CORSMiddleware` only if the resulting list has valid elements.

## 2026-03-27 - Unbounded Numeric Input DoS Risk

**Vulnerability:** The application accepted unbounded numeric inputs for `temperature`, `top_p`, `presence_penalty`, and `frequency_penalty` fields in the `Input` API payload. This exposed the system to Denial of Service (DoS) attacks or unpredictable behavior during downstream AI inference if given logically invalid or extremely large values.
**Learning:** While string and list lengths are commonly limited to prevent DoS, numeric fields must also be strictly bounded to logically valid ranges to prevent downstream errors or excessive resource consumption.
**Prevention:** Use Pydantic's `Field(ge=..., le=...)` constraints to explicitly restrict all numeric fields to their expected valid ranges (e.g., `temperature` 0.0 to 2.0).

## 2026-03-30 - DoS Risk via Unbounded Image URL Object

**Vulnerability:** The application accepted an unbounded dictionary `Dict[str, str]` for the `image_url` property in the `ContentImage` model. This exposed the system to Denial of Service (DoS) attacks via memory exhaustion by allowing attackers to send payloads with massive base64 strings or an enormous number of keys.
**Learning:** Pydantic's generic typing (like `Dict[str, str]`) provides no length or size constraints. For large, potentially malicious input like base64 image representations, explicitly bounded models are critical to prevent memory starvation and excessive JSON parsing overhead.
**Prevention:** Replace unbounded dictionary types with strongly typed Pydantic sub-models (e.g., `ImageUrl`). Enforce strict `max_length` constraints on all fields (e.g., `url: str = Field(max_length=5000000)`) to validate and restrict the payload size at the schema level.

## 2025-05-15 - Information Leakage in Streaming Error Responses

**Vulnerability:** The application was leaking raw error messages to clients in SSE streams in `src/interface/http/handlers.rs`. This could expose internal details of failures to attackers.
**Learning:** Directly formatting error strings into streaming response chunks is insecure. Errors should be logged internally and masked for the client.
**Prevention:** Return a generic error message (e.g., "An error occurred while processing the request.") in the SSE stream while logging the specific error details server-side.

## 2025-05-15 - Application Panic via Malformed CORS Configuration

**Vulnerability:** The application would panic and fail to start if the `ALLOWED_ORIGINS` environment variable contained malformed origins, due to an unsafe `.unwrap()` in `src/interface/http/middleware.rs`.
**Learning:** Trusting environment variables to always be correctly formatted is a risk. Configuration parsing must be defensive to avoid Denial of Service (DoS) at the application level.
**Prevention:** Use safe parsing (e.g., `.parse().ok()`) and `filter_map` when processing comma-separated configuration values. Return `None` or a safe default if no valid values are found.

## 2026-08-07 - Information Leakage via JSON Validation Rejection

**Vulnerability:** The `ValidatedJson` extractor in `src/interface/http/validation.rs` was returning raw deserialization error messages `rejection.to_string()` directly to the client under the `"details"` key. This could leak internal application architecture, precise struct names, expected types, and fragments of untrusted input.
**Learning:** Returning raw parser error messages is a common vector for information disclosure. Clients only need to know that their request was malformed, while detailed error logs should be kept secure on the server.
**Prevention:** Intercept JSON deserialization rejections, log the detailed validation message internally via `tracing::error!`, and return generic, sanitized messages to the client (e.g., indicating the payload size limit exceeded or general JSON schema invalidity).
