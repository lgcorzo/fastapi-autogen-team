---
type: class
title: "R2RTool"
source_path: "src/infrastructure/tools/r2r.rs"
description: "Documentation for src/infrastructure/tools/r2r.rs."
tags: [class, rust, tool]
last_verified_commit: "1997254"
---
Source File: `src/infrastructure/tools/r2r.rs`

## Component Overview

This module defines the `R2RTool` component which integrates with the Rig framework to execute vector searches in the R2R RAG system.

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
        +NAME: &'static str
        +definition(String _prompt) ToolDefinition
        +call(R2RArgs args) Result~String_R2RError~
    }

    class Functions {
        <<module>>
        +get_r2r_results(String url, String query) Result~String_anyhow::Error~
    }
```

### Execution Flow
```mermaid
sequenceDiagram
    participant Agent
    participant R2RTool
    participant R2RAPI

    Agent->>R2RTool: call(args)
    R2RTool->>R2RTool: get env R2R_URL (fallback: http://r2r:7272)
    R2RTool->>R2RAPI: get_r2r_results(url, query)

    R2RAPI->>R2RAPI: get env R2R_USER, R2R_PWD
    R2RAPI->>R2RAPI: build login URL (/v3/users/login)
    R2RAPI-->>R2RAPI: POST with credentials
    R2RAPI-->>R2RAPI: Parse access_token

    R2RAPI->>R2RAPI: build search URL (/v3/retrieval/search)
    R2RAPI-->>R2RAPI: POST query with Bearer Token & Vector settings
    R2RAPI-->>R2RAPI: JSON Response
    R2RAPI-->>R2RAPI: Parse chunk_search_results

    R2RTool-->>Agent: Concatenated Chunk Texts or "No result found"
```

## Dependencies
- `rig::completion::ToolDefinition`
- `rig::tool::Tool`
- `serde::Deserialize`
- `serde_json::json`
- `std::env`
- `thiserror::Error`
- `reqwest`
- `anyhow`