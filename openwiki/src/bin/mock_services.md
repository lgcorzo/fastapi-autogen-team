---
type: "module-architecture"
title: "Mock_services"
description: "Technical architecture and class hierarchy for Mock_services"
tags: ["architecture", "uml", "pyreverse", "openwiki"]
timestamp: "2026-07-31T08:02:02Z"
---

# Module Name: Mock_services

* **Source Directory Reference:** `src/bin/`
* **Package Dependency:**
- `axum::{`
- `serde::Deserialize`
- `serde_json::{json, Value}`
- `std::net::SocketAddr`
- `std::sync::Arc`
- `tracing_subscriber::{layer::SubscriberExt, util::SubscriberInitExt}`

## 1. Executive Summary & Purpose
Deterministic technical architecture for the `Mock_services` module extracted directly from the codebase.

## 2. UML 2.0 Class & Inheritance Architecture (Deterministic)
The following class diagram models the object-oriented structure, explicit inheritance hierarchies, and polymorphic interface implementations derived from local AST analysis:

```mermaid
classDiagram
    direction BT
    class AppState {
    }
    class JiraQueryParams {
        +Option~String~, jql
    }
    JiraQueryParams --> Option : Association
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
    participant Svc as AppState
    Caller->>Svc: main()
    Svc->>Svc: registry()
    Svc->>Svc: with()
    Svc->>Svc: layer()
    Svc-->>Caller: Returns execution status
    Caller->>Svc: r2r_login()
    Svc->>Svc: Json()
    Svc-->>Caller: Returns execution status
    Caller->>Svc: r2r_rag()
    Svc->>Svc: Json()
    Svc-->>Caller: Returns execution status
    Caller->>Svc: r2r_search()
    Svc->>Svc: Json()
    Svc-->>Caller: Returns execution status
    Caller->>Svc: jira_search()
    Svc->>Svc: Json()
    Svc-->>Caller: Returns execution status
```


---

* **Source Citations:**
* Class `AppState`: `src/bin/mock_services.rs:13`
* Class `JiraQueryParams`: `src/bin/mock_services.rs:77`
* Method `main`: `src/bin/mock_services.rs:16`
* Method `r2r_login`: `src/bin/mock_services.rs:40`
* Method `r2r_rag`: `src/bin/mock_services.rs:51`
* Method `r2r_search`: `src/bin/mock_services.rs:60`
* Method `jira_search`: `src/bin/mock_services.rs:81`
