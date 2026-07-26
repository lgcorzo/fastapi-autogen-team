---
type: class
title: "Search"
source_path: "src/infrastructure/tools/search.rs"
description: "Documentation for src/infrastructure/tools/search.rs."
tags: [class, rust]
last_verified_commit: "cf3c1ee"
---
Source File: `src/infrastructure/tools/search.rs`

## Component Overview

This module defines the `Search` component.

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
        +NAME: &'static str$
        +definition(String prompt) ToolDefinition
        +call(SearchArgs args) Result~SearchResult_SearchError~
    }
```

### Execution Flow
```mermaid
flowchart TD
    Start --> definition
    definition --> call
    call --> End
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
