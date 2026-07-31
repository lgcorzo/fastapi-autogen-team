---
type: "module-architecture"
title: "Jira"
description: "Technical architecture, API specification, and UML 2.0 diagrams for Jira"
tags: ["architecture", "uml2", "okf", "openwiki", "polyglot"]
timestamp: "2026-07-31T12:51:19Z"
---

# Module Architecture: Jira

* **Source File Reference:** `src/infrastructure/tools/jira.rs`
* **Package Dependencies:** Upstream: `[[ToolDefinition]]` | `[[Tool]]` | `[[Deserialize]]` | `[[json]]` | `[[env]]` | `[[Error]]`

## 1. Executive Summary & Purpose
Deterministic technical architecture for the `Jira` module extracted directly from the codebase.

## 2. UML 2.0 Diagrams

### Class / Struct Architecture
```mermaid
classDiagram
    direction BT
    class JiraArgs {
        +String, query
    }
    class JiraError {
        <<enumeration>>
    }
    JiraArgs --> String : Association
    Tool <|.. JiraTool : Realization
```


### Runtime Sequence Diagram
```mermaid
sequenceDiagram
    autonumber
    participant Caller as Client Interface
    participant Svc as JiraArgs
    Caller->>Svc: get_jira_results()
    Svc->>Svc: var()
    Svc->>Svc: var()
    Svc->>Svc: new()
    Svc-->>Caller: Returns execution status
```


## 3. Data Structures, Structs & Class Properties

| Property / Field | Type | Visibility | Description | Source Reference |
| :--- | :--- | :--- | :--- | :--- |
| `query` | `String,` | Public (`+`) | Extracted property query. | `src/infrastructure/tools/jira.rs:9` |


## 4. Comprehensive Methods & Functions Breakdown

### Function / Method: `get_jira_results(url: &str, query: &str)`
* **Source Reference:** `src/infrastructure/tools/jira.rs:56`
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
* Module File: `src/infrastructure/tools/jira.rs`
* Class `JiraArgs`: `src/infrastructure/tools/jira.rs:9`
* Enum `JiraError`: `src/infrastructure/tools/jira.rs:14`
* Method `get_jira_results`: `src/infrastructure/tools/jira.rs:56`
