---
type: class
title: "Team"
source_path: "src/domain/agent/team.rs"
description: "Documentation for src/domain/agent/team.rs."
tags: [class, rust]
last_verified_commit: "cf3c1ee"
---
Source File: `src/domain/agent/team.rs`

## Component Overview

This module defines the `Team` component.

## Architecture

### Class Diagram
```mermaid
classDiagram
    class AgentEvent {
        <<enumeration>>
        Progress
        Delta
        Done
    }

    class AgentTeam {
        -openai::Client client
        +new() Result~Self_anyhow::Error~$
        +new_mock() Self$
        +new_test(String base_url) Self$
        +run(Input input) Result~String_anyhow::Error~
        +run_stream(Input input) Stream~Item_Result_AgentEvent_Infallible_~
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

## Dependencies
- `crate::application::dtos::Input`
- `crate::infrastructure::tools::confluence::ConfluenceTool`
- `crate::infrastructure::tools::jira::JiraTool`
- `crate::infrastructure::tools::r2r::R2RTool`
- `async_stream::stream`
- `futures::{future::join_all, Stream, StreamExt}`
- `rig::agent::MultiTurnStreamItem`
- `rig::client::CompletionClient`
- `rig::completion::Prompt`
- `rig::providers::openai`
- `rig::streaming::{StreamedAssistantContent, StreamingPrompt}`
- `serde_json`
- `std::env`
- `std::pin::Pin`
