# Detailed Architecture Guide

This document explains the relationship between the various elements of the `fastapi-autogen-team` project, following the **Domain-Driven Design (DDD)** standard.

## DDD Layer Mapping

The project is structured into four distinct layers to ensure a clean separation of concerns and maintainability.

### 1. Interface Layer (`src/interface/`)
Handles the communication with external clients (REST API). 
- **`handlers.rs`**: Processes incoming HTTP requests and delegates work to the Domain layer.
- **`routes.rs`**: Manages the application router and state.
- **`middleware.rs`**: Implements security headers, CORS, and request sanitization.

### 2. Application Layer (`src/application/`)
Defines the data formats and transformations used within the application.
- **`dtos.rs`**: Data Transfer Objects (DTOs) that represent the API contracts (OpenAI-compatible).

### 3. Domain Layer (`src/domain/`)
The core of the system. Contains the business logic and orchestrates the multi-agent team.
- **`AgentTeam`**: The central aggregate that coordinates the Planner, Searcher, and QA agents to solve user queries.

### 4. Infrastructure Layer (`src/infrastructure/`)
Provides technical capabilities and interfaces with external services.
- **`tools/`**: Contains the specific implementation for Jira and R2R search tools.
- **`telemetry.rs`**: Handles observability (OpenTelemetry, tracing).

---

## Structural UML (Class Diagram)

This diagram shows the structural relationship between the core components of the service.

```mermaid
classDiagram
    direction TB
    class AppState {
        +Arc~AgentTeam~ team
    }

    class Handlers {
        +route_query(State, Json)
        +get_models()
    }

    class AgentTeam {
        +openai::Client client
        +run(Input) String
        +run_stream(Input) Stream
        -PlannerAgent planner
        -SearcherAgent searcher
        -QAAgent qa
    }

    class SearchTool {
        +call(SearchArgs) SearchResult
    }

    class Tool {
        <<interface>>
        +definition()
        +call()
    }

    class Input {
        +String model
        +Vec~Message~ messages
    }

    Handlers --> AppState : Uses
    AppState --> AgentTeam : Contains
    AgentTeam "1" *-- "Multi" Tool : Orchestrates
    SearchTool ..|> Tool : Implements
    AgentTeam ..> Input : Processes
```

---

## Execution Flow (Sequence Diagram)

This diagram details the lifecycle of a single query through the multi-agent system.

```mermaid
sequenceDiagram
    participant User
    participant H as Handler (Interface)
    participant T as AgentTeam (Domain)
    participant P as Planner Agent
    participant S as Searcher Agent
    participant I as Infrastructure Tool
    participant QA as QA Agent

    User->>H: POST /chat/completions (Input)
    H->>T: run(Input)
    T->>P: Analyze Goal & Decompose
    P-->>T: Queries (List of search strings)
    
    loop For Each Query
        T->>S: Execute search for Query
        S->>I: Fetch external data (Jira/R2R)
        I-->>S: Raw Data
        S-->>T: Search Context
    end

    T->>QA: Synthesize Context & Answer
    QA-->>T: Final Response (Markdown)
    T-->>H: Result String
    H-->>User: JSON Response (OpenAI compatible)
```

---

## Multi-Agent Workflow (Flowchart)

A detailed look at the decision logic within the `AgentTeam`.

```mermaid
graph TD
    Start([User Request]) --> Plan[Planner Agent]
    Plan --> Q1{Queries generated?}
    Q1 -- No --> Error[Retry / Default Response]
    Q1 -- Yes --> LoopStart[Iterate through search queries]

    LoopStart --> RAG[RAG Searcher Agent]
    RAG --> Tool[Invoke search Tool]
    Tool --> Jira[Fetch Jira status]
    Tool --> R2R[Fetch RAG results]
    Jira --> Context[Accumulate ContextBuffer]
    R2R --> Context[Accumulate ContextBuffer]
    
    Context --> Q2{More queries?}
    Q2 -- Yes --> LoopStart
    Q2 -- No --> Synthesis[QA Agent Synthesis]
    
    Synthesis --> Terminate{Contains 'TERMINATE'?}
    Terminate -- No --> Refine[Refine Output]
    Refine --> Synthesis
    Terminate -- Yes --> Final[Return to Interface Layer]
    Final --> End([Send JSON to User])
```
