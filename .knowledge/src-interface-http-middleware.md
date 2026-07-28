---
type: module
title: "HTTP Middleware"
source_path: "src/interface/http/middleware.rs"
description: "Documentation for src/interface/http/middleware.rs."
tags: [module, rust, web, security]
last_verified_commit: "cfcd09b"
---
Source File: `src/interface/http/middleware.rs`

## Component Overview

This module provides Axum middleware layers for adding standard HTTP security headers and configuring Cross-Origin Resource Sharing (CORS).

## Architecture

### Class Diagram
```mermaid
classDiagram
    class Middleware {
        <<module>>
        +security_headers() Vec~SetResponseHeaderLayer_HeaderValue_~
        +cors_layer() Option~CorsLayer~
    }
```

### Execution Flow
```mermaid
flowchart TD
    Req[Incoming Request] --> CORS[cors_layer: Check ALLOWED_ORIGINS]
    CORS --> Handlers[Axum Route Handlers]
    Handlers --> SecHeaders[security_headers: Set NOSNIFF, DENY, HSTS, CSP]
    SecHeaders --> Res[Outgoing Response]
```

## Dependencies
- `axum::http::{HeaderName, HeaderValue}`
- `std::env`
- `tower_http::cors::{AllowOrigin, CorsLayer}`
- `tower_http::set_header::SetResponseHeaderLayer`