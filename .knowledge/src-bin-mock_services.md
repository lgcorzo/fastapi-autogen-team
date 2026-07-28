---
type: script
title: "MockServices"
source_path: "src/bin/mock_services.rs"
description: "Documentation for src/bin/mock_services.rs."
tags: [script, rust]
last_verified_commit: "cfcd09b"
---
Source File: `src/bin/mock_services.rs`

## Component Overview

This module defines the `MockServices` component.

## Architecture

### Class Diagram
```mermaid
classDiagram
    class AppState
    class JiraQueryParams
```

### Execution Flow
```mermaid
flowchart TD
    Start --> main
    main --> r2r_login
    r2r_login --> r2r_rag
    r2r_rag --> r2r_search
    r2r_search --> jira_search
    jira_search --> End
```

## Dependencies
- `axum::{ extract::Query, routing::{get, post}, Json, Router, }`
- `serde::Deserialize`
- `serde_json::{json, Value}`
- `std::net::SocketAddr`
- `std::sync::Arc`
- `tracing_subscriber::{layer::SubscriberExt, util::SubscriberInitExt}`
