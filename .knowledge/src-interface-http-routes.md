---
type: api
title: "Routes"
source_path: "src/interface/http/routes.rs"
description: "Documentation for src/interface/http/routes.rs."
tags: [api, rust]
last_verified_commit: "cf3c1ee"
---
Source File: `src/interface/http/routes.rs`

## Component Overview

This module defines the `Routes` component.

## Architecture

### Class Diagram
```mermaid
classDiagram
    class AppState
```

### Execution Flow
```mermaid
flowchart TD
    Start --> create_app
    create_app --> End
```

## Dependencies
- `crate::domain::agent::team::AgentTeam`
- `crate::interface::http::handlers::{docs_redirect, get_models, route_query}`
- `crate::interface::http::middleware::{cors_layer, security_headers}`
- `axum::{ routing::{get, post}, Router, }`
- `std::sync::Arc`
- `tower_http::trace::TraceLayer`
