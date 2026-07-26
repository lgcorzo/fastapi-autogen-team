---
type: class
title: "AgentTeam"
description: "Core orchestrator for multi-agent workflows handling RAG searches and query synthesis."
tags: [domain, agent, orchestration, llm]
last_verified_commit: "722dbbe"
---

# agent-team.rs

This module defines the `AgentTeam` which orchestrates multi-agent tasks, handling streaming (`run_stream`) and non-streaming (`run`) operations for the LLM pipeline, integrating search tools.

```mermaid
classDiagram
    class AgentEvent {
        <<enumeration>>
        Progress(String stage, String message)
        Delta(String)
        Done
    }

    class AgentTeam {
        -openai::Client client
        +new() Result~Self, anyhow::Error~$
        +new_mock() Self$
        +new_test(String base_url) Self$
        +run(Input input) Result~String, anyhow::Error~
        +run_stream(Input input) Stream~Item = Result~AgentEvent, Infallible~~
    }
```

### Execution Flow

```mermaid
sequenceDiagram
    participant Client
    participant AgentTeam
    participant PlannerAgent
    participant SearchTools
    participant ExpertAgent

    Client->>AgentTeam: run(input) / run_stream(input)
    AgentTeam->>PlannerAgent: Generate independent search queries
    PlannerAgent-->>AgentTeam: List of queries

    loop For each valid query
        AgentTeam->>SearchTools: Execute searches (R2R, Jira, Confluence)
        SearchTools-->>AgentTeam: Aggregated Results
        AgentTeam->>Client: (Streaming) emit Progress
    end

    AgentTeam->>ExpertAgent: Synthesize final answer using search results
    ExpertAgent-->>AgentTeam: Synthesized Response / Streamed Tokens

    alt Streaming Mode
        AgentTeam->>Client: emit Delta(tokens)
        AgentTeam->>Client: emit Done
    else Non-Streaming Mode
        AgentTeam-->>Client: Final complete String
    end
```
