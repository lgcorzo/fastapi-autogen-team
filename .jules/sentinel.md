
## 2026-01-20 - Exception Leakage in Helper Tools
**Vulnerability:** Helper functions in `src/fastapi_autogen_team/tool.py` (`safe_get_r2r_results`, `safe_get_jira_results`) were catching exceptions and returning `f"Error...: {e}"`. This return value was passed back to the LLM agent and potentially to the user, leaking internal error details.
**Learning:** Security sanitation must apply to all layers, not just the API surface. Helper functions that return strings to be consumed by LLMs or users must also fail securely.
**Prevention:** Catch exceptions in helper functions, log them with `exc_info=True`, and return a generic error message string.
