## 2025-05-24 - Prompt Injection via CRLF Bypass
**Vulnerability:** The prompt sanitization logic in `sanitize_for_prompt` used string replacement on specific sequences like `\n},\n`. However, it did not normalize line endings, allowing attackers to bypass the check by using CRLF (`\r\n`) sequences, which the LLM interprets as newlines but the sanitizer missed.
**Learning:** String-based sanitization must account for all variations of control characters, especially line endings which can vary across systems and inputs.
**Prevention:** Always normalize line endings (e.g., to `\n`) before applying structural sanitization or validation logic. Use robust normalization functions at the entry point of data processing.
