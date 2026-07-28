---
type: class
title: "ConfluenceTool"
source_path: "src/infrastructure/tools/confluence.rs"
description: "Documentation for src/infrastructure/tools/confluence.rs."
tags: [class, rust, tool]
last_verified_commit: "cfcd09b"
---
Source File: `src/infrastructure/tools/confluence.rs`

## Component Overview

This module defines the `ConfluenceTool` component which integrates with the Rig framework to execute searches in Confluence using CQL.

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
        +NAME: &'static str
        +definition(String _prompt) ToolDefinition
        +call(ConfluenceArgs args) Result~String_ConfluenceError~
    }

    class Functions {
        <<module>>
        +get_confluence_results(String url, String query) Result~String_anyhow::Error~
    }
```

### Execution Flow
```mermaid
sequenceDiagram
    participant Agent
    participant ConfluenceTool
    participant ConfluenceAPI

    Agent->>ConfluenceTool: call(args)
    ConfluenceTool->>ConfluenceTool: get env JIRA_INSTANCE_URL
    ConfluenceTool->>ConfluenceAPI: get_confluence_results(url, query)
    ConfluenceAPI->>ConfluenceAPI: build CQL (text ~ "query" OR title ~ "query")
    ConfluenceAPI->>ConfluenceAPI: build URL (append /wiki/rest/api/content/search)
    ConfluenceAPI-->>ConfluenceAPI: GET with Basic Auth
    ConfluenceAPI-->>ConfluenceTool: JSON Response
    ConfluenceTool-->>Agent: Formatted List of Confluence Pages or "No results"
```

## Dependencies
- `rig::completion::ToolDefinition`
- `rig::tool::Tool`
- `serde::Deserialize`
- `serde_json::json`
- `std::env`
- `thiserror::Error`
