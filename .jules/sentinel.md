## 2024-05-23 - Information Leakage in Error Responses
**Vulnerability:** Exception messages were being returned directly to the API client in `HTTPException` details.
**Learning:** Catching broad `Exception` and interpolating `e` into the response detail exposes internal implementation details (paths, query fragments, etc.) to potential attackers.
**Prevention:** Always catch exceptions, log the full traceback (`exc_info=True`), but return a generic, static error message to the client (e.g., "An internal error occurred").
