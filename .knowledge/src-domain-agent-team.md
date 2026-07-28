---
type: class
title: "Team"
source_path: "src/domain/agent/team.rs"
description: "Documentation for src/domain/agent/team.rs."
tags: [class, rust]
last_verified_commit: "cfcd09b"
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
    participant LanguageDetector
    participant Translator
    participant PlannerAgent
    participant SearchTools
    participant ExpertAgent

    Client->>AgentTeam: run(input) / run_stream(input)

    par Language Processing
        AgentTeam->>LanguageDetector: Detect input language
        AgentTeam->>Translator: Translate to English (if needed)
    end

    AgentTeam->>Client: (Streaming) emit Progress (Language Detected & Translated)

    AgentTeam->>PlannerAgent: Generate up to 5 independent search queries based on English text
    PlannerAgent-->>AgentTeam: List of queries tagged with [JIRA], [CONFLUENCE], or [R2R]

    AgentTeam->>Client: (Streaming) emit Progress (Planner queries generated)

    loop For each valid query (up to 5)
        alt is [JIRA]
            AgentTeam->>SearchTools: Jira Search
        else is [CONFLUENCE]
            AgentTeam->>SearchTools: Confluence Search
        else is [R2R] or Default
            AgentTeam->>SearchTools: R2R Search
        end

        SearchTools-->>AgentTeam: Search Results
        AgentTeam->>Client: (Streaming) emit Progress (Search completed)
    end

    AgentTeam->>ExpertAgent: Synthesize final answer using search results & translate back to original language
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
