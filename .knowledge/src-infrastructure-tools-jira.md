---
type: class
title: "Jira"
source_path: "src/infrastructure/tools/jira.rs"
description: "Documentation for src/infrastructure/tools/jira.rs."
tags: [class, rust]
last_verified_commit: "cf3c1ee"
---
Source File: `src/infrastructure/tools/jira.rs`

## Component Overview

This module defines the `Jira` component.

## Architecture

### Class Diagram
```mermaid
classDiagram
    class JiraArgs {
        +String query
    }

    class JiraError {
        <<enumeration>>
        EnvVarMissing(VarError)
        RequestError(reqwest::Error)
        Other(String)
    }

    class JiraTool {
        +NAME: &'static str$
        +definition(String prompt) ToolDefinition
        +call(JiraArgs args) Result~String, JiraError~
    }
```

### Execution Flow
```mermaid
flowchart TD
    Start --> definition
    definition --> call
    call --> get_jira_results
    get_jira_results --> End
```

## Dependencies
- `rig::completion::ToolDefinition`
- `rig::tool::Tool`
- `serde::Deserialize`
- `serde_json::json`
- `std::env`
- `thiserror::Error`
