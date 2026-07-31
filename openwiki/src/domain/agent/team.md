---
type: "module-architecture"
title: "Team"
description: "Technical architecture and class hierarchy for Team"
tags: ["architecture", "uml", "pyreverse", "openwiki"]
timestamp: "2026-07-30T20:32:40Z"
---

# Module Name: Team

* **Source Directory Reference:** `src/domain/agent/`
* **Package Dependency:**
- `async_stream::stream`
- `crate::application::dtos::Input`
- `crate::infrastructure::tools::confluence::ConfluenceTool`
- `crate::infrastructure::tools::jira::JiraTool`
- `crate::infrastructure::tools::r2r::R2RTool`
- `futures::{future::join_all, Stream, StreamExt}`
- `rig::agent::MultiTurnStreamItem`
- `rig::client::CompletionClient`
- `rig::completion::Prompt`
- `rig::providers::openai`
- `rig::streaming::{StreamedAssistantContent, StreamingPrompt}`
- `serde_json`
- `std::env`
- `std::pin::Pin`

## 1. Executive Summary & Purpose
Deterministic technical architecture for the `Team` module extracted directly from the codebase.

## 2. UML 2.0 Class & Inheritance Architecture (Deterministic)
The following class diagram models the object-oriented structure, explicit inheritance hierarchies, and polymorphic interface implementations derived from local AST analysis:

```mermaid
classDiagram
    direction BT
    class AgentTeam {
        +openai::Client, client
        +new()
        +run()
        +new_mock()
        +new_test()
    }
    class AgentEvent {
        <<enumeration>>
        Progress
    }
```


## 3. Package & Class Relations

* **Inheritance & Polymorphism:** Detailed breakdown of abstract base classes, interfaces, and concrete overrides.
* **Dependencies:** How classes within this package collaborate externally.

## 4. Execution Flow & Runtime Behavior

The following sequence diagram outlines the execution lifecycle and message passing during core operations:

```mermaid
sequenceDiagram
    autonumber
    participant Caller as Client Interface
    participant Svc as AgentTeam
    Caller->>Svc: new()
    Svc->>Svc: var()
    Svc->>Svc: expect()
    Svc->>Svc: var()
    Svc-->>Caller: Returns execution status
    Caller->>Svc: run()
    Svc->>Svc: clone()
    Svc->>Svc: completions_api()
    Svc->>Svc: last()
    Svc-->>Caller: Returns execution status
    Caller->>Svc: new_mock()
    Svc-->>Caller: Returns execution status
    Caller->>Svc: new_test()
    Svc->>Svc: builder()
    Svc->>Svc: api_key()
    Svc->>Svc: base_url()
    Svc-->>Caller: Returns execution status
    Caller->>Svc: is_valid_query_line()
    Svc->>Svc: trim()
    Svc->>Svc: len()
    Svc->>Svc: starts_with()
    Svc-->>Caller: Returns execution status
```


---

* **Source Citations:**
* Class `AgentTeam`: `src/domain/agent/team.rs:51`
* Class `AgentEvent`: `src/domain/agent/team.rs:23`
* Method `new` in `AgentTeam`: `src/domain/agent/team.rs:55`
* Method `run` in `AgentTeam`: `src/domain/agent/team.rs:66`
* Method `new_mock` in `AgentTeam`: `src/domain/agent/team.rs:454`
* Method `new_test` in `AgentTeam`: `src/domain/agent/team.rs:463`
* Method `is_valid_query_line`: `src/domain/agent/team.rs:32`
