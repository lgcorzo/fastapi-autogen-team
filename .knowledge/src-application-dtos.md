---
type: class
title: "Dtos"
source_path: "src/application/dtos.rs"
description: "Documentation for src/application/dtos.rs."
tags: [class, rust]
last_verified_commit: "cf3c1ee"
---
Source File: `src/application/dtos.rs`

## Component Overview

This module defines the `Dtos` component.

## Architecture

### Class Diagram
```mermaid
classDiagram
    class ImageUrl {
        +String url
        +Option~String~ detail
    }

    class Content {
        <<enumeration>>
        Image
        Text
    }
    Content *-- ImageUrl : contains

    class ModelInformation {
        +String id
        +String name
        +String description
        +HashMap~String_Value~ pricing
        +u32 context_length
        +HashMap~String_Value~ architecture
        +HashMap~String_Value~ top_provider
        +Option~HashMap_String_Value_~ per_request_limits
    }

    class Message {
        +String role
        +ContentType content
        +Option~String~ name
    }
    Message *-- ContentType : contains

    class ContentType {
        <<enumeration>>
        String
        List
    }
    ContentType *-- Content : contains list of

    class Input {
        +String model
        +Option~String~ user
        +Vec~Message~ messages
        +Option~f32~ temperature
        +Option~f32~ top_p
        +Option~f32~ presence_penalty
        +Option~f32~ frequency_penalty
        +Option~bool~ stream
    }
    Input *-- Message : contains list of

    class Output {
        +String id
        +String object
        +i64 created
        +String model
        +Vec~HashMap_String_Value_~ choices
        +HashMap~String_Value~ usage
        +default() Output$
    }
```

### Execution Flow
```mermaid
flowchart TD
    Start --> default_node["default"]
    default_node["default"] --> End
```

## Dependencies
- `serde::{Deserialize, Serialize}`
- `serde_json::Value`
- `std::collections::HashMap`
