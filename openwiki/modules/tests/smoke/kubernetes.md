---
iso_doc_type: "Specification"
iso_viewpoint: "ComponentView"
type: "module"
title: "Module: Kubernetes"
source_path: "tests/smoke/kubernetes.rs"
description: "Detailed architecture and specifications for the Kubernetes module."
tags: ["core", "module", "okf", "iso42010"]
last_verified_commit: "a4e0af3"
timestamp: "2026-08-27T21:46:14Z"
---

# Module Specification: Kubernetes

* **Source Reference:** `tests/smoke/kubernetes.rs`
* **Package Dependency:**
- `use dotenvy::dotenv;`
- `use futures::StreamExt;`
- `use rust_agent_team::application::dtos::{ContentType, Input, Message};`
- `use rust_agent_team::domain::agent::team::{AgentEvent, AgentTeam};`
- `use std::env;`

## 1. Executive Summary & Purpose
Deterministic technical architecture for the `Kubernetes` module extracted directly from the codebase.

## 2. UML 2.0 Diagrams
### Class & Inheritance Architecture
```plantuml
@startuml
    class Kubernetes {
        <<module>>
        +is_in_kubernetes()
        +run_kubernetes_agent_test()
        +test_r2r_access_in_kubernetes()
        +test_jira_access_in_kubernetes()
        +test_confluence_access_in_kubernetes()
        +test_all_tools_access_in_kubernetes()
    }
@enduml
```


### Execution Flow & Runtime Behavior
```plantuml
@startuml
    autonumber
    participant "Client Interface" as Caller
    participant Kubernetes as Svc
    Caller->Svc: is_in_kubernetes()
    Svc->Svc: is_ok()
    Svc->Svc: env::var()
    Svc-->Caller: Returns execution status
    Caller->Svc: run_kubernetes_agent_test()
    Svc->Svc: is_in_kubernetes()
    Svc->Svc: ok()
    Svc->Svc: dotenv()
    Svc-->Caller: Returns execution status
    Caller->Svc: test_r2r_access_in_kubernetes()
    Svc->Svc: run_kubernetes_agent_test()
    Svc-->Caller: Returns execution status
    Caller->Svc: test_jira_access_in_kubernetes()
    Svc->Svc: run_kubernetes_agent_test()
    Svc-->Caller: Returns execution status
    Caller->Svc: test_confluence_access_in_kubernetes()
    Svc->Svc: run_kubernetes_agent_test()
    Svc-->Caller: Returns execution status
@enduml
```


## 3. Data Structures, Structs & Class Properties

### Kubernetes


## 4. Comprehensive Methods & Functions Breakdown

### `is_in_kubernetes`
* **Visibility:** -
* **Source Line Citation:** `tests/smoke/kubernetes.rs:L8`

**Purpose:** Helper function to determine if the test is running inside a Kubernetes cluster.

#### Parameters
| Parameter | Type |
| :--- | :--- |
| None | None |

#### Return value
- `bool`

### `run_kubernetes_agent_test`
* **Visibility:** -
* **Source Line Citation:** `tests/smoke/kubernetes.rs:L13`

**Purpose:** Helper function to run the agent team with a specific prompt and check if a specific tool was triggered.

#### Parameters
| Parameter | Type |
| :--- | :--- |
| `prompt` | `&str` |
| `expected_tool_indicator` | `&str` |

#### Return value
- `()`

### `test_r2r_access_in_kubernetes`
* **Visibility:** -
* **Source Line Citation:** `tests/smoke/kubernetes.rs:L106`

**Purpose:** PRODUCTION TEST: Verify that the agent successfully accesses R2R (RAG) information inside Kubernetes.

#### Parameters
| Parameter | Type |
| :--- | :--- |
| None | None |

#### Return value
- `()`

### `test_jira_access_in_kubernetes`
* **Visibility:** -
* **Source Line Citation:** `tests/smoke/kubernetes.rs:L117`

**Purpose:** PRODUCTION TEST: Verify that the agent successfully accesses JIRA information inside Kubernetes.

#### Parameters
| Parameter | Type |
| :--- | :--- |
| None | None |

#### Return value
- `()`

### `test_confluence_access_in_kubernetes`
* **Visibility:** -
* **Source Line Citation:** `tests/smoke/kubernetes.rs:L128`

**Purpose:** PRODUCTION TEST: Verify that the agent successfully accesses Confluence information inside Kubernetes.

#### Parameters
| Parameter | Type |
| :--- | :--- |
| None | None |

#### Return value
- `()`

### `test_all_tools_access_in_kubernetes`
* **Visibility:** -
* **Source Line Citation:** `tests/smoke/kubernetes.rs:L139`

**Purpose:** PRODUCTION TEST: Verify that the agent successfully accesses ALL three systems in a single prompt.

#### Parameters
| Parameter | Type |
| :--- | :--- |
| None | None |

#### Return value
- `()`



## 5. Source Code Citations & Index
* Class `Kubernetes`: `tests/smoke/kubernetes.rs:L1`
* Method `is_in_kubernetes`: `tests/smoke/kubernetes.rs:L8`
* Method `run_kubernetes_agent_test`: `tests/smoke/kubernetes.rs:L13`
* Method `test_r2r_access_in_kubernetes`: `tests/smoke/kubernetes.rs:L106`
* Method `test_jira_access_in_kubernetes`: `tests/smoke/kubernetes.rs:L117`
* Method `test_confluence_access_in_kubernetes`: `tests/smoke/kubernetes.rs:L128`
* Method `test_all_tools_access_in_kubernetes`: `tests/smoke/kubernetes.rs:L139`
