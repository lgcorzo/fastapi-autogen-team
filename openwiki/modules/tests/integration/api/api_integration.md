---
iso_doc_type: "Specification"
iso_viewpoint: "ComponentView"
type: "module"
title: "Module: Api_integration"
source_path: "tests/integration/api/api_integration.rs"
description: "Detailed architecture and specifications for the Api_integration module."
tags: ["core", "module", "okf", "iso42010"]
last_verified_commit: "e0059f3"
timestamp: "2026-08-18T20:35:50Z"
---

# Module Specification: Api_integration

* **Source Reference:** `tests/integration/api/api_integration.rs`
* **Package Dependency:**
- `use axum::{
    body::Body,
    http::{self, Request, StatusCode},
};`
- `use http_body_util::BodyExt;`
- `use mockito::Server;`
- `use rust_agent_team::application::dtos::{ContentType, Input, Message};`
- `use rust_agent_team::domain::agent::team::AgentTeam;`
- `use rust_agent_team::{create_app, AppState};`
- `use serde_json::Value;`
- `use std::env;`
- `use std::sync::Arc;`
- `use tower::ServiceExt;`

## 1. Executive Summary & Purpose
Deterministic technical architecture for the `Api_integration` module extracted directly from the codebase.

## 2. UML 2.0 Diagrams
### Class & Inheritance Architecture
```plantuml
@startuml
    class Api_integration {
        <<module>>
        +test_docs_redirect()
        +test_get_models()
        +test_chat_completions_route()
        +setup_pipeline_mocks()
        +test_chat_completions_streaming_sse()
    }
@enduml
```


### Execution Flow & Runtime Behavior
```plantuml
@startuml
    autonumber
    participant "Client Interface" as Caller
    participant Api_integration as Svc
    Caller->Svc: test_docs_redirect()
    Svc->Svc: AgentTeam::new_mock()
    Svc->Svc: Arc::new()
    Svc->Svc: create_app()
    Svc-->Caller: Returns execution status
    Caller->Svc: test_get_models()
    Svc->Svc: AgentTeam::new_mock()
    Svc->Svc: Arc::new()
    Svc->Svc: create_app()
    Svc-->Caller: Returns execution status
    Caller->Svc: test_chat_completions_route()
    Svc->Svc: Server::new_async()
    Svc->Svc: url()
    Svc->Svc: env::set_var()
    Svc-->Caller: Returns execution status
    Caller->Svc: setup_pipeline_mocks()
    Svc->Svc: create_async()
    Svc->Svc: expect()
    Svc->Svc: with_body()
    Svc-->Caller: Returns execution status
    Caller->Svc: test_chat_completions_streaming_sse()
    Svc->Svc: Server::new_async()
    Svc->Svc: url()
    Svc->Svc: env::set_var()
    Svc-->Caller: Returns execution status
@enduml
```


## 3. Data Structures, Structs & Class Properties

### Api_integration


## 4. Comprehensive Methods & Functions Breakdown

### `test_docs_redirect`
* **Visibility:** -
* **Source Line Citation:** `tests/integration/api/api_integration.rs:L16`

#### Input Parameters
| Parameter | Data Type | Required / Default | Semantic Description |
| :--- | :--- | :--- | :--- |
| None | None | N/A | No parameters |

#### Return Value & Output Shape
| Return Type | Scenario | Description |
| :--- | :--- | :--- |
| `()` | Success | Result of the operation |

### `test_get_models`
* **Visibility:** -
* **Source Line Citation:** `tests/integration/api/api_integration.rs:L39`

#### Input Parameters
| Parameter | Data Type | Required / Default | Semantic Description |
| :--- | :--- | :--- | :--- |
| None | None | N/A | No parameters |

#### Return Value & Output Shape
| Return Type | Scenario | Description |
| :--- | :--- | :--- |
| `()` | Success | Result of the operation |

### `test_chat_completions_route`
* **Visibility:** -
* **Source Line Citation:** `tests/integration/api/api_integration.rs:L64`

#### Input Parameters
| Parameter | Data Type | Required / Default | Semantic Description |
| :--- | :--- | :--- | :--- |
| None | None | N/A | No parameters |

#### Return Value & Output Shape
| Return Type | Scenario | Description |
| :--- | :--- | :--- |
| `()` | Success | Result of the operation |

### `setup_pipeline_mocks`
* **Visibility:** -
* **Source Line Citation:** `tests/integration/api/api_integration.rs:L223`

**Description:** Builds the full set of mockito mocks for the three-agent pipeline.

#### Input Parameters
| Parameter | Data Type | Required / Default | Semantic Description |
| :--- | :--- | :--- | :--- |
| `server` | `&mut Server` | Required | Parameter |

#### Return Value & Output Shape
| Return Type | Scenario | Description |
| :--- | :--- | :--- |
| `Vec<mockito::Mock>` | Success | Result of the operation |

### `test_chat_completions_streaming_sse`
* **Visibility:** -
* **Source Line Citation:** `tests/integration/api/api_integration.rs:L315`

#### Input Parameters
| Parameter | Data Type | Required / Default | Semantic Description |
| :--- | :--- | :--- | :--- |
| None | None | N/A | No parameters |

#### Return Value & Output Shape
| Return Type | Scenario | Description |
| :--- | :--- | :--- |
| `()` | Success | Result of the operation |



## 5. Source Code Citations & Index
* Class `Api_integration`: `tests/integration/api/api_integration.rs:L1`
* Method `test_docs_redirect`: `tests/integration/api/api_integration.rs:L16`
* Method `test_get_models`: `tests/integration/api/api_integration.rs:L39`
* Method `test_chat_completions_route`: `tests/integration/api/api_integration.rs:L64`
* Method `setup_pipeline_mocks`: `tests/integration/api/api_integration.rs:L223`
* Method `test_chat_completions_streaming_sse`: `tests/integration/api/api_integration.rs:L315`
