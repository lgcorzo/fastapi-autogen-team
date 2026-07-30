---
type: "module-architecture"
title: "R2r"
description: "Technical architecture and class hierarchy for R2r"
tags: ["architecture", "uml", "pyreverse", "openwiki"]
timestamp: "2026-07-30T20:32:40Z"
---

# Module Name: R2r

* **Source Directory Reference:** `src/infrastructure/tools/`
* **Package Dependency:**
- `rig::completion::ToolDefinition`
- `rig::tool::Tool`
- `serde::Deserialize`
- `serde_json::json`
- `std::env`
- `thiserror::Error`

## 1. Executive Summary & Purpose
Deterministic technical architecture for the `R2r` module extracted directly from the codebase.

## 2. UML 2.0 Class & Inheritance Architecture (Deterministic)
The following class diagram models the object-oriented structure, explicit inheritance hierarchies, and polymorphic interface implementations derived from local AST analysis:

```mermaid
classDiagram
    direction BT
    class R2RArgs {
        +String, query
    }
    class R2RError {
        <<enumeration>>
    }
    R2RArgs --> String : Association
    Tool <|.. R2RTool : Realization
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
    participant Svc as R2RArgs
    Caller->>Svc: get_r2r_results()
    Svc->>Svc: var()
    Svc->>Svc: var()
    Svc->>Svc: new()
    Svc-->>Caller: Returns execution status
```


---

* **Source Citations:**
* Class `R2RArgs`: `src/infrastructure/tools/r2r.rs:9`
* Class `R2RError`: `src/infrastructure/tools/r2r.rs:14`
* Method `get_r2r_results`: `src/infrastructure/tools/r2r.rs:57`
