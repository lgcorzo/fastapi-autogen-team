---
type: class
title: "SearchTool"
source_path: "src/infrastructure/tools/search.rs"
description: "Documentation for src/infrastructure/tools/search.rs."
tags: [class, rust, tool]
last_verified_commit: "cfcd09b"
---
Source File: `src/infrastructure/tools/search.rs`

## Component Overview

This module defines the `SearchTool` component which provides a unified interface to search across R2R, Jira, and Confluence sequentially.

## Architecture

### Class Diagram
```mermaid
classDiagram
    class SearchArgs {
        +String query
    }

    class SearchResult {
        +String r2r
        +String jira
        +String confluence
    }

    class SearchError {
        <<enumeration>>
        EnvVarMissing
        RequestError
        Other
    }

    class SearchTool {
        +NAME: &'static str
        +definition(String _prompt) ToolDefinition
        +call(SearchArgs args) Result~SearchResult_SearchError~
    }
```

### Execution Flow
```mermaid
sequenceDiagram
    participant Agent
    participant SearchTool
    participant R2R
    participant Jira
    participant Confluence

    Agent->>SearchTool: call(args)

    SearchTool->>SearchTool: get env R2R_URL and JIRA_INSTANCE_URL

    SearchTool->>R2R: get_r2r_results(r2r_url, query)
    R2R-->>SearchTool: R2R Results

    SearchTool->>Jira: get_jira_results(jira_url, query)
    Jira-->>SearchTool: Jira Results

    SearchTool->>Confluence: get_confluence_results(jira_url, query)
    Confluence-->>SearchTool: Confluence Results

    SearchTool-->>Agent: SearchResult { r2r, jira, confluence }
```

## Dependencies
- `crate::infrastructure::tools::confluence::get_confluence_results`
- `crate::infrastructure::tools::jira::get_jira_results`
- `crate::infrastructure::tools::r2r::get_r2r_results`
- `rig::completion::ToolDefinition`
- `rig::tool::Tool`
- `serde::{Deserialize, Serialize}`
- `serde_json::json`
- `std::env`
- `thiserror::Error`