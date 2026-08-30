---
iso_doc_type: "Specification"
iso_viewpoint: "ComponentView"
type: "module"
title: "Module: Team"
source_path: "src/domain/agent/team.rs"
description: "Detailed architecture and specifications for the Team module."
tags: ["core", "module", "okf", "iso42010"]
last_verified_commit: "7a5d2bc"
timestamp: "2026-08-30T20:43:56Z"
---

# Module Specification: Team

* **Source Reference:** `src/domain/agent/team.rs`
* **Package Dependency:**
- `use async_stream::stream;`
- `use crate::application::dtos::Input;`
- `use crate::infrastructure::tools::confluence::ConfluenceTool;`
- `use crate::infrastructure::tools::jira::JiraTool;`
- `use crate::infrastructure::tools::r2r::R2RTool;`
- `use futures::{future::join_all, Stream, StreamExt};`
- `use rig::agent::MultiTurnStreamItem;`
- `use rig::client::CompletionClient;`
- `use rig::completion::Prompt;`
- `use rig::providers::openai;`
- `use rig::streaming::{StreamedAssistantContent, StreamingPrompt};`
- `use serde_json;`
- `use std::env;`
- `use std::pin::Pin;`

## 1. Executive Summary & Purpose
Deterministic technical architecture for the `Team` module extracted directly from the codebase.

## 2. UML 2.0 Diagrams
### Class & Inheritance Architecture
```plantuml
@startuml
    class AgentEvent {
        <<enumeration>>
        Progress
        Delta
        Done
    }
    class AgentTeam {
        -client: openai::Client
        +new()
        +run()
        +run_stream()
        +new_mock()
        +new_test()
    }
@enduml
```


### Execution Flow & Runtime Behavior
```plantuml
@startuml
    autonumber
    participant "Client Interface" as Caller
    participant AgentEvent as Svc
    Caller->Svc: is_valid_query_line()
    Svc->Svc: trim()
    Svc->Svc: len()
    Svc->Svc: starts_with()
    Svc-->Caller: Returns execution status
    Caller->Svc: new()
    Svc->Svc: expect()
    Svc->Svc: env::var()
    Svc->Svc: unwrap_or_else()
    Svc-->Caller: Returns execution status
    Caller->Svc: run()
    Svc->Svc: completions_api()
    Svc->Svc: clone()
    Svc->Svc: unwrap_or_default()
    Svc-->Caller: Returns execution status
    Caller->Svc: run_stream()
    Svc->Svc: clone()
    Svc->Svc: completions_api()
    Svc->Svc: Box::pin()
    Svc-->Caller: Returns execution status
    Caller->Svc: new_mock()
    Svc->Svc: unwrap()
    Svc->Svc: build()
    Svc->Svc: base_url()
    Svc-->Caller: Returns execution status
@enduml
```


## 3. Data Structures, Structs & Class Properties

### AgentEvent
**Overview:** Events emitted by the agent pipeline during SSE streaming.

`Progress` events are emitted after the planner and each RAG search.
`Delta` events carry individual QA token chunks.
`Done` signals end-of-stream.
Progress events are **only** produced on the streaming path (`run_stream`).

| Property | Type | Description |
| :--- | :--- | :--- |
| `Progress` | `variant(stage: String, message: String)` | Field of AgentEvent |
| `Delta` | `variant(String)` | Field of AgentEvent |
| `Done` | `variant` | Field of AgentEvent |

### AgentTeam
| Property | Type | Description |
| :--- | :--- | :--- |
| `client` | `openai::Client` | Field of AgentTeam |



## 4. Comprehensive Methods & Functions Breakdown

### `is_valid_query_line`
* **Visibility:** -
* **Source Line Citation:** `src/domain/agent/team.rs:L32`

**Purpose:** Returns `true` when a planner output line is a valid standalone search query.
Rejects: empty lines, JSON structural tokens, quoted strings, the literal
TERMINATE keyword, and lines that are too short to be meaningful queries.

#### Parameters
| Parameter | Type | Description |
| :--- | :--- | :--- |
| `line` | `&str` | Parameter |

#### Return value
`bool`

### `AgentTeam::new`
* **Visibility:** +
* **Source Line Citation:** `src/domain/agent/team.rs:L56`

**Description:** No description provided.

#### Inputs
| Parameter | Data Type | Required / Default | Semantic Description |
| :--- | :--- | :--- | :--- |
| None | None | N/A | No parameters |

#### Output
| Return Type | Scenario | Description |
| :--- | :--- | :--- |
| `anyhow::Result<Self>` | Success | Result of the operation |

#### Side Effects
None identified.

#### Complexity
- **Time Complexity:** O(1) (Estimated)
- **Space Complexity:** O(1) (Estimated)

#### Example
```rust
// Example usage
```

### `AgentTeam::run`
* **Visibility:** +
* **Source Line Citation:** `src/domain/agent/team.rs:L69`

**Description:** No description provided.

#### Inputs
| Parameter | Data Type | Required / Default | Semantic Description |
| :--- | :--- | :--- | :--- |
| `&self` | `self` | Required | Instance reference |
| `input` | `Input` | Required | Parameter |

#### Output
| Return Type | Scenario | Description |
| :--- | :--- | :--- |
| `anyhow::Result<String>` | Success | Result of the operation |

#### Side Effects
None identified.

#### Complexity
- **Time Complexity:** O(1) (Estimated)
- **Space Complexity:** O(1) (Estimated)

#### Example
```rust
// Example usage
```

### `AgentTeam::run_stream`
* **Visibility:** +
* **Source Line Citation:** `src/domain/agent/team.rs:L245`

**Description:** Run the agent pipeline with full SSE progress streaming.

Emits:
- `AgentEvent::Progress` after the planner stage and after each RAG search.
- `AgentEvent::Delta` for each streaming token from the QA agent.
- `AgentEvent::Done` once all tokens have been emitted.

Progress events are **not** produced by the non-streaming `run()` method.

#### Inputs
| Parameter | Data Type | Required / Default | Semantic Description |
| :--- | :--- | :--- | :--- |
| `&self` | `self` | Required | Instance reference |
| `input` | `Input` | Required | Parameter |

#### Output
| Return Type | Scenario | Description |
| :--- | :--- | :--- |
| `anyhow::Result<Pin<Box<dyn Stream<Item = anyhow::Result<AgentEvent>> + Send>>>` | Success | Result of the operation |

#### Side Effects
None identified.

#### Complexity
- **Time Complexity:** O(1) (Estimated)
- **Space Complexity:** O(1) (Estimated)

#### Example
```rust
// Example usage
```

### `AgentTeam::new_mock`
* **Visibility:** +
* **Source Line Citation:** `src/domain/agent/team.rs:L457`

**Description:** No description provided.

#### Inputs
| Parameter | Data Type | Required / Default | Semantic Description |
| :--- | :--- | :--- | :--- |
| None | None | N/A | No parameters |

#### Output
| Return Type | Scenario | Description |
| :--- | :--- | :--- |
| `Self` | Success | Result of the operation |

#### Side Effects
None identified.

#### Complexity
- **Time Complexity:** O(1) (Estimated)
- **Space Complexity:** O(1) (Estimated)

#### Example
```rust
// Example usage
```

### `AgentTeam::new_test`
* **Visibility:** +
* **Source Line Citation:** `src/domain/agent/team.rs:L466`

**Description:** No description provided.

#### Inputs
| Parameter | Data Type | Required / Default | Semantic Description |
| :--- | :--- | :--- | :--- |
| `base_url` | `&str` | Required | Parameter |

#### Output
| Return Type | Scenario | Description |
| :--- | :--- | :--- |
| `Self` | Success | Result of the operation |

#### Side Effects
None identified.

#### Complexity
- **Time Complexity:** O(1) (Estimated)
- **Space Complexity:** O(1) (Estimated)

#### Example
```rust
// Example usage
```



## 5. Source Code Citations & Index
* Class `AgentEvent`: `src/domain/agent/team.rs:L23`
* Class `AgentTeam`: `src/domain/agent/team.rs:L51`
* Method `is_valid_query_line`: `src/domain/agent/team.rs:L32`
* Method `new` in `AgentTeam`: `src/domain/agent/team.rs:L56`
* Method `run` in `AgentTeam`: `src/domain/agent/team.rs:L69`
* Method `run_stream` in `AgentTeam`: `src/domain/agent/team.rs:L245`
* Method `new_mock` in `AgentTeam`: `src/domain/agent/team.rs:L457`
* Method `new_test` in `AgentTeam`: `src/domain/agent/team.rs:L466`
