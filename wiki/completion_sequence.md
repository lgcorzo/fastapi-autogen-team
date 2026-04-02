# Completion Sequence

The diagram below details the end-to-end lifecycle of a `/chat/completions` request.

![Chat Sequence](chat_completion_sequence.plantuml)

---

## 🚦 Request Lifecycle

1.  **API Extraction**: Axum extracts the query, model, and message history from the POST request.
2.  **Team Initialized**: The `AgentTeam` creates a new orchestration session.
3.  **Planning Phase**: The **Planner Agent** decides which tools are necessary.
4.  **Action Phase**: The **Searcher Agent** concurrently (where possible) executes the tool calls.
5.  **Quality Check**: The **QA Agent** reviews the compiled context and synthesizes the user's answer.
6.  **Streaming Delivery**: The result is streamed back to the user via **Tokio channels**.
