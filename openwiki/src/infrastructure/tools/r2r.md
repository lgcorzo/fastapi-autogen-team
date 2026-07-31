---
type: "module-architecture"
title: "R2r"
description: "Technical architecture, API specification, and UML 2.0 diagrams for R2r"
tags: ["architecture", "uml2", "okf", "openwiki", "polyglot"]
timestamp: "2026-07-31T12:51:19Z"
---

# Module Architecture: R2r

* **Source File Reference:** `src/infrastructure/tools/r2r.rs`
* **Package Dependencies:** Upstream: `[[ToolDefinition]]` | `[[Tool]]` | `[[Deserialize]]` | `[[json]]` | `[[env]]` | `[[Error]]`

## 1. Executive Summary & Purpose
Deterministic technical architecture for the `R2r` module extracted directly from the codebase.

## 2. UML 2.0 Diagrams

### Class / Struct Architecture
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


### Runtime Sequence Diagram
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


## 3. Data Structures, Structs & Class Properties

| Property / Field | Type | Visibility | Description | Source Reference |
| :--- | :--- | :--- | :--- | :--- |
| `query` | `String,` | Public (`+`) | Extracted property query. | `src/infrastructure/tools/r2r.rs:9` |


## 4. Comprehensive Methods & Functions Breakdown

### Function / Method: `get_r2r_results(url: &str, query: &str)`
* **Source Reference:** `src/infrastructure/tools/r2r.rs:57`
* **Visibility / Scope:** Public (`+`)
* **Behavioral Overview:** Extracted method logic.

#### Input Parameters
| Parameter | Type | Required / Default | Description |
| :--- | :--- | :--- | :--- |
| `url` | `&str` | Required | Derived parameter. |
| `query` | `&str` | Required | Derived parameter. |

#### Output & Return Values
| Return Type | Condition / Scenario | Description |
| :--- | :--- | :--- |
| `anyhow::Result<String>` | Standard Execution | Derived return type. |




---

## 5. Source Code Citations & Index
* Module File: `src/infrastructure/tools/r2r.rs`
* Class `R2RArgs`: `src/infrastructure/tools/r2r.rs:9`
* Enum `R2RError`: `src/infrastructure/tools/r2r.rs:14`
* Method `get_r2r_results`: `src/infrastructure/tools/r2r.rs:57`
