---
type: module
title: "HTTP Handlers"
source_path: "src/interface/http/handlers.rs"
description: "Documentation for src/interface/http/handlers.rs."
tags: [module, rust, web]
last_verified_commit: "1997254"
---
Source File: `src/interface/http/handlers.rs`

## Component Overview

This module contains the Axum HTTP handlers for the application API, primarily routing requests to the domain agent and formatting responses.

## Architecture

### Class Diagram
```mermaid
classDiagram
    class Handlers {
        <<module>>
        +docs_redirect() impl IntoResponse
        +get_models() impl IntoResponse
        +route_query(State state, HeaderMap headers, ValidatedJson request) impl IntoResponse
    }
```

### Execution Flow
```mermaid
sequenceDiagram
    participant Client
    participant Handlers
    participant ValidatedJson
    participant AgentTeam

    Client->>Handlers: POST /chat/completions (route_query)
    Handlers->>ValidatedJson: extract and validate request
    alt Invalid Request
        ValidatedJson-->>Client: 422 Unprocessable Entity
    else Valid Request
        alt stream == true
            Handlers->>AgentTeam: run_stream(request)
            AgentTeam-->>Handlers: Stream of AgentEvents (Progress, Delta, Done)
            loop over stream
                Handlers->>Handlers: Map AgentEvent to chat.completion.chunk JSON
                Handlers-->>Client: Yield SSE Event
            end
        else stream == false
            Handlers->>AgentTeam: run(request)
            AgentTeam-->>Handlers: Result string
            Handlers-->>Client: Return JSON chat.completion
        end
    end
```

## Dependencies
- `axum::{extract::State, http::{HeaderMap, StatusCode}, response::{sse::Event, IntoResponse, Sse}, Json}`
- `futures::StreamExt`
- `serde_json::json`
- `std::convert::Infallible`
- `std::sync::Arc`
- `crate::application::dtos::Input`
- `crate::domain::agent::team::AgentEvent`
- `crate::interface::http::routes::AppState`
- `crate::interface::http::validation::ValidatedJson`