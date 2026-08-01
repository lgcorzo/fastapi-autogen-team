# Request Completion Sequence (DDD)

The following diagram illustrates the request lifecycle as it traverses the Domain-Driven Design (DDD) layers of the service. 

---

## 🔄 Interaction Lifecycle

```mermaid
sequenceDiagram
    participant C as Client
    participant I as "Interface (Axum)"
    participant A as "Application (DTOs)"
    participant D as "Domain (AgentTeam)"
    participant Inf as "Infrastructure (Tools)"


    Note over C,Inf: 1. Request Entry
    C->>I: POST /chat/completions
    I->>A: Deserialize JSON to DTO
    
    Note over I,D: 2. Core Orchestration
    I->>D: Invoke AgentTeam::run_stream
    D->>D: Planner: Define Tasks
    
    loop Agentic Search & Retrieval
        D->>Inf: Searcher: Execute Tool
        Inf->>Inf: Connect to Jira/R2R
        Inf-->>D: Return Context
    end

    Note over D,I: 3. Synthesis & Streaming
    D->>D: QA: Final Verification
    D-->>I: Yield SSE Token Chunks
    
    Note over I,C: 4. Final Response
    I-->>C: Stream SSE Events 
```

---

## 🛠️ Key State Transitions
1. **Serialization**: `Interface` -> `Application` (Raw JSON to Typed DTO).
2. **Orchestration**: `Interface` -> `Domain` (HTTP Context to Business Logic).
3. **Retrieval**: `Domain` -> `Infrastructure` (Domain Query to Technical Client).
4. **Streaming**: `Domain` -> `Interface` (Logic Result to Web Protocol).
