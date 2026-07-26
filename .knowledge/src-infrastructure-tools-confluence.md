---
type: class
title: "Confluence"
source_path: "src/infrastructure/tools/confluence.rs"
description: "Documentation for src/infrastructure/tools/confluence.rs."
tags: [class, rust]
last_verified_commit: "cf3c1ee"
---
Source File: `src/infrastructure/tools/confluence.rs`

## Component Overview

This module defines the `Confluence` component.

## Architecture

### Class Diagram
```mermaid
classDiagram
    class ConfluenceArgs {
        +String query
    }

    class ConfluenceError {
        <<enumeration>>
        EnvVarMissing
        RequestError
        Other
    }

    class ConfluenceTool {
        +NAME: &'static str$
        +definition(String prompt) ToolDefinition
        +call(ConfluenceArgs args) Result~String_ConfluenceError~
    }
```

### Execution Flow
```mermaid
flowchart TD
    Start --> definition
    definition --> call_node["call"]
    call_node["call"] --> get_confluence_results
    get_confluence_results --> End
```

## Dependencies
- `rig::completion::ToolDefinition`
- `rig::tool::Tool`
- `serde::Deserialize`
- `serde_json::json`
- `std::env`
- `thiserror::Error`
