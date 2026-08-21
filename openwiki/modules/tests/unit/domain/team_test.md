---
iso_doc_type: "Specification"
iso_viewpoint: "ComponentView"
type: "module"
title: "Module: Team_test"
source_path: "tests/unit/domain/team_test.rs"
description: "Detailed architecture and specifications for the Team_test module."
tags: ["core", "module", "okf", "iso42010"]
last_verified_commit: "631f244"
timestamp: "2026-08-21T20:15:09Z"
---

# Module Specification: Team_test

* **Source Reference:** `tests/unit/domain/team_test.rs`
* **Package Dependency:**
- `use futures::StreamExt;`
- `use mockito::Server;`
- `use rust_agent_team::application::dtos::{ContentType, Input, Message};`
- `use rust_agent_team::domain::agent::team::AgentTeam;`

## 1. Executive Summary & Purpose
Deterministic technical architecture for the `Team_test` module extracted directly from the codebase.

## 2. UML 2.0 Diagrams
### Class & Inheritance Architecture
```plantuml
@startuml
    class Team_test {
        <<module>>
        +make_input()
        +test_agent_team_run_error()
        +test_agent_team_run_stream_error_on_planner_failure()
    }
@enduml
```


### Execution Flow & Runtime Behavior
```plantuml
@startuml
    autonumber
    participant "Client Interface" as Caller
    participant Team_test as Svc
    Caller->Svc: make_input()
    Svc->Svc: to_string()
    Svc-->Caller: Returns execution status
    Caller->Svc: test_agent_team_run_error()
    Svc->Svc: Server::new_async()
    Svc->Svc: url()
    Svc->Svc: AgentTeam::new_test()
    Svc-->Caller: Returns execution status
    Caller->Svc: test_agent_team_run_stream_error_on_planner_failure()
    Svc->Svc: Server::new_async()
    Svc->Svc: url()
    Svc->Svc: AgentTeam::new_test()
    Svc-->Caller: Returns execution status
@enduml
```


## 3. Data Structures, Structs & Class Properties

### Team_test


## 4. Comprehensive Methods & Functions Breakdown

### `make_input`
* **Visibility:** -
* **Source Line Citation:** `tests/unit/domain/team_test.rs:L5`

#### Input Parameters
| Parameter | Data Type | Required / Default | Semantic Description |
| :--- | :--- | :--- | :--- |
| `text` | `&str` | Required | Parameter |

#### Return Value & Output Shape
| Return Type | Scenario | Description |
| :--- | :--- | :--- |
| `Input` | Success | Result of the operation |

### `test_agent_team_run_error`
* **Visibility:** -
* **Source Line Citation:** `tests/unit/domain/team_test.rs:L23`

#### Input Parameters
| Parameter | Data Type | Required / Default | Semantic Description |
| :--- | :--- | :--- | :--- |
| None | None | N/A | No parameters |

#### Return Value & Output Shape
| Return Type | Scenario | Description |
| :--- | :--- | :--- |
| `()` | Success | Result of the operation |

### `test_agent_team_run_stream_error_on_planner_failure`
* **Visibility:** -
* **Source Line Citation:** `tests/unit/domain/team_test.rs:L39`

#### Input Parameters
| Parameter | Data Type | Required / Default | Semantic Description |
| :--- | :--- | :--- | :--- |
| None | None | N/A | No parameters |

#### Return Value & Output Shape
| Return Type | Scenario | Description |
| :--- | :--- | :--- |
| `()` | Success | Result of the operation |



## 5. Source Code Citations & Index
* Class `Team_test`: `tests/unit/domain/team_test.rs:L1`
* Method `make_input`: `tests/unit/domain/team_test.rs:L5`
* Method `test_agent_team_run_error`: `tests/unit/domain/team_test.rs:L23`
* Method `test_agent_team_run_stream_error_on_planner_failure`: `tests/unit/domain/team_test.rs:L39`
