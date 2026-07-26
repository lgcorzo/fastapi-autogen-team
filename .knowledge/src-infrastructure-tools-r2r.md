---
type: class
title: "R2R"
source_path: "src/infrastructure/tools/r2r.rs"
description: "Documentation for src/infrastructure/tools/r2r.rs."
tags: [class, rust]
last_verified_commit: "cf3c1ee"
---
Source File: `src/infrastructure/tools/r2r.rs`

## Component Overview

This module defines the `R2R` component.

## Architecture

### Class Diagram
```mermaid
classDiagram
    class R2RArgs {
        +String query
    }

    class R2RError {
        <<enumeration>>
        EnvVarMissing
        RequestError
        Other
    }

    class R2RTool {
        +NAME: &'static str$
        +definition(String prompt) ToolDefinition
        +call(R2RArgs args) Result~String_R2RError~
    }
```

### Execution Flow
```mermaid
flowchart TD
    Start --> definition
    definition --> call_node["call"]
    call_node["call"] --> get_r2r_results
    get_r2r_results --> End
```

## Dependencies
- `rig::completion::ToolDefinition`
- `rig::tool::Tool`
- `serde::Deserialize`
- `serde_json::json`
- `std::env`
- `thiserror::Error`
