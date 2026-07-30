---
type: "module-architecture"
title: "Dtos"
description: "Technical architecture and class hierarchy for Dtos"
tags: ["architecture", "uml", "pyreverse", "openwiki"]
timestamp: "2026-07-30T19:23:37Z"
---

# Module Name: Dtos

* **Source Directory Reference:** `src/application/`
* **Package Dependency:**
- `serde::{Deserialize, Serialize}`
- `serde_json::Value`
- `std::collections::HashMap`

## 1. Executive Summary & Purpose
Deterministic technical architecture for the `Dtos` module extracted directly from the codebase.

## 2. UML 2.0 Class & Inheritance Architecture (Deterministic)
The following class diagram models the object-oriented structure, explicit inheritance hierarchies, and polymorphic interface implementations derived from local AST analysis:

```mermaid
classDiagram
    direction BT
    class ImageUrl {
        +String, url
        +Option~String~, detail
    }
    class ModelInformation {
        +String, id
        +String, name
        +String, description
        +HashMap~String,_Value~, pricing
        +u32, context_length
        +HashMap~String,_Value~, architecture
        +HashMap~String,_Value~, top_provider
        +Option~HashMap~String,_Value~~, per_request_limits
    }
    class Message {
        +String, role
        +ContentType, content
        +Option~String~, name
    }
    class Input {
        +String, model
        +Option~String~, user
        +Vec~Message~, messages
        +Option~f32~, temperature
        +Option~f32~, top_p
        +Option~f32~, presence_penalty
        +Option~f32~, frequency_penalty
        +Option~bool~, stream
    }
    class Output {
        +String, id
        +String, object
        +i64, created
        +String, model
        +Vec~HashMap~String,_Value~~, choices
        +HashMap~String,_Value~, usage
        -default()
    }
    class Content {
        <<enumeration>>
        Image
    }
    class ContentType {
        <<enumeration>>
        String
        List
    }
    Default <|.. Output : Realization
```


## 3. Package & Class Relations

* **Inheritance & Polymorphism:** Diagram depicts detected traits, realizations, and abstractions.
* **Dependencies:** Defined by import structures across the boundary.

## 4. Execution Flow & Runtime Behavior

The following sequence diagram outlines the execution lifecycle and message passing during core operations:

```mermaid
sequenceDiagram
    autonumber
    participant Caller as Client Interface
    participant Svc as ImageUrl
```


---

* **Source Citations:**
* Class `ImageUrl`: `src/application/dtos.rs:6`
* Class `ModelInformation`: `src/application/dtos.rs:22`
* Class `Message`: `src/application/dtos.rs:34`
* Class `Input`: `src/application/dtos.rs:48`
* Class `Output`: `src/application/dtos.rs:61`
* Class `Content`: `src/application/dtos.rs:13`
* Class `ContentType`: `src/application/dtos.rs:42`
* Method `default` in `Output`: `src/application/dtos.rs:70`
