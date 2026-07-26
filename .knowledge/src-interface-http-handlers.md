---
type: api
title: "Handlers"
source_path: "src/interface/http/handlers.rs"
description: "Documentation for src/interface/http/handlers.rs."
tags: [api, rust]
last_verified_commit: "cf3c1ee"
---
Source File: `src/interface/http/handlers.rs`

## Component Overview

This module defines the `Handlers` component.

## Architecture

### Class Diagram
```mermaid
classDiagram
    class EmptyComponent
```

### Execution Flow
```mermaid
flowchart TD
    Req["Incoming HTTP Request"]

    Req --> RouteQuery["route_query()"]
    Req --> GetModels["get_models()"]
    Req --> DocsRedirect["docs_redirect()"]

    RouteQuery --> Validate["Validate JSON Input"]
    Validate -- Valid --> AgentRun{"Is Streaming?"}
    Validate -- Invalid --> ErrorResp["400 Bad Request"]

    AgentRun -- Stream = true --> AgentTeamRunStream["AgentTeam::run_stream()"]
    AgentTeamRunStream --> EmitSSE["Yield SSE Events"]
    EmitSSE --> ResponseStream["Streaming Response"]

    AgentRun -- Stream = false / None --> AgentTeamRun["AgentTeam::run()"]
    AgentTeamRun --> JsonResponse["JSON Completion Output"]

    GetModels --> StaticModels["Return hardcoded mock model data"]

    DocsRedirect --> Http303["303 See Other Redirect"]
```

## Dependencies
- `axum::{ extract::State, http::{HeaderMap, StatusCode}, response::{sse::Event, IntoResponse, Sse}, Json, }`
- `futures::StreamExt`
- `serde_json::json`
- `std::convert::Infallible`
- `std::sync::Arc`
- `crate::application::dtos::Input`
- `crate::domain::agent::team::AgentEvent`
- `crate::interface::http::routes::AppState`
- `crate::interface::http::validation::ValidatedJson`
