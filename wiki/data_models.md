# Data Models

The following diagram illustrates the primary Rust structs used for state management and API communication.

![Data Models Diagram](data_models.plantuml)

---

## 🏗️ Core Structs

### AppState
The global state shared across all Axum handlers. It contains the initialized `AgentTeam` and the necessary API configurations for Jira and R2R.

### AgentInput
The structured request body for the `/chat/completions` endpoint. It closely follows the OpenAI specification but leverages Rust's safety for optional fields and strictly typed message roles.

### AgentOutput
The standardized response format. When streaming is disabled, this object encapsulates the full completion, including usage statistics.
