# V2 System Architecture (Rust)

## 🏗️ High-Level Design
The system has been redesigned as a modular, asynchronous Rust service. It follows a clean architecture pattern, separating the web interface, the agentic orchestration logic, and the external tool integrations.

---

### [Axum API Layer]
The entry point of the service is a REST API built with **Axum**. It manages:
- **AppState**: Centralized state management for the `AgentTeam`, environment configuration, and sharing it across request handlers.
- **Handlers**: The `/chat/completions` endpoint uses **Tokio channels** to stream partial tokens back to the client in real-time.
- **Safety**: Robust error handling via `axum::response::IntoResponse` and `anyhow`.

---

### [Agent Orchestration (Rig)]
At the heart of the service is the `AgentTeam`, implemented in `src/agents.rs`. It utilizes the **Rig** framework to orchestrate a triad of specialized agents:

1.  **Planner Agent**: 
    - Analyzes the initial user request.
    - Breaks the problem into logical steps and tool calls.
    - Orchestrated through Rig's `Agent` trait.
2.  **Searcher Agent**:
    - Possesses a suite of **Tools** (Jira, R2R).
    - Executes precise queries based on the Planner's instructions.
    - Gathers relevant context for the final generation.
3.  **QA Agent**:
    - Reviews the raw response and gathered context.
    - Ensures the output meets quality standards.
    - Finalizes the message for the user.

---

### [Tool Integrations]
Our tools are implemented as Rust structs that conform to Rig's `Tool` trait, allowing the agents to call them autonomously.

#### 📁 R2R (Retrieval-Augmented Generation)
- **Engine**: R2R (Neo4j/Vector DB).
- **Functionality**: Performs vector similarity search across indexed documents to provide the LLM with grounded facts.

#### 🎫 Jira (Project Management)
- **Engine**: Atlassian Jira Rest API.
- **Functionality**: Lists, searches, and summarizes Jira issues to keep the agent team informed about task status.

---

## 🚦 Request Lifecycle

1.  **Request**: User sends a POST to `/chat/completions`.
2.  **Dispatch**: Axum extracts the query and passes it to the `AgentTeam`.
3.  **Planning**: The Planner agent determines if local search or Jira is required.
4.  **Action**: The Searcher agent executes the tool(s) and retrieves context.
5.  **Synthesis**: The QA agent formats the response.
6.  **Response**: The result is streamed or returned as a JSON object to the user.

---

## 🛠️ Module Structure
- `src/main.rs`: Entry point and server initialization.
- `src/lib.rs`: Shared library and Axum router setup.
- `src/agents.rs`: Rig Agent definitions and orchestration logic.
- `src/tools.rs`: External API integrations (Jira, R2R).
- `src/data_model.rs`: Serde-ready structs for API and internal communication.
