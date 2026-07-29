---
type: class
title: "JiraTool"
source_path: "src/infrastructure/tools/jira.rs"
description: "Documentation for src/infrastructure/tools/jira.rs."
tags: [class, rust, tool]
last_verified_commit: "cfcd09b"
---
Source File: `src/infrastructure/tools/jira.rs`

## Component Overview

This module defines the `JiraTool` component which integrates with the Rig framework to execute searches in Jira using JQL.

## Architecture

### Class Diagram
```mermaid
classDiagram
    class JiraArgs {
        +String query
    }

    class JiraError {
        <<enumeration>>
        EnvVarMissing
        RequestError
        Other
    }

    class JiraTool {
        +NAME: &'static str
        +definition(String _prompt) ToolDefinition
        +call(JiraArgs args) Result~String_JiraError~
    }

    class Functions {
        <<module>>
        +get_jira_results(String url, String query) Result~String_anyhow::Error~
    }
```

### Execution Flow
```mermaid
sequenceDiagram
    participant Agent
    participant JiraTool
    participant JiraAPI

    Agent->>JiraTool: call(args)
    JiraTool->>JiraTool: get env JIRA_INSTANCE_URL
    JiraTool->>JiraAPI: get_jira_results(url, query)
    JiraAPI->>JiraAPI: sanitize query

    alt query contains issue keys (e.g. PROJ-123)
        JiraAPI->>JiraAPI: extract keys and build JQL with 'key =' condition
    else query is normal text
        JiraAPI->>JiraAPI: build JQL (summary ~ "query" OR description ~ "query")
    end

    JiraAPI->>JiraAPI: build URL (append /rest/api/3/search/jql)
    JiraAPI-->>JiraAPI: GET with Basic Auth
    JiraAPI-->>JiraTool: JSON Response
    JiraTool-->>Agent: Formatted List of Jira Issues or "No results"
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