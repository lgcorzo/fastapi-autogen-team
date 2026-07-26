---
type: module
title: "Middleware"
source_path: "src/interface/http/middleware.rs"
description: "Documentation for src/interface/http/middleware.rs."
tags: [module, rust]
last_verified_commit: "cf3c1ee"
---
Source File: `src/interface/http/middleware.rs`

## Component Overview

This module defines the `Middleware` component.

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

    Req --> MiddlewareStack["Axum Middleware Stack"]

    MiddlewareStack --> CorsLayer["cors_layer()"]
    CorsLayer --> CheckEnv{"ALLOWED_ORIGINS"}
    CheckEnv -- Not Set / Empty --> DenyCors["No CORS Layer Appended"]
    CheckEnv -- "*" --> AllowAll["Allow All Origins"]
    CheckEnv -- "Specific Domains" --> ParseOrigins["Parse HeaderValues safely"]
    ParseOrigins --> AllowSpecific["Allow Configured Origins"]

    MiddlewareStack --> SecurityHeaders["security_headers()"]
    SecurityHeaders --> AddHeaders["Append Static Security Headers"]

    AddHeaders --> ContentTypeOptions["X-Content-Type-Options: nosniff"]
    AddHeaders --> FrameOptions["X-Frame-Options: DENY"]
    AddHeaders --> HSTS["Strict-Transport-Security: max-age=..."]
    AddHeaders --> CSP["Content-Security-Policy: default-src 'self'..."]
    AddHeaders --> ReferrerPolicy["Referrer-Policy: strict-origin-when-cross-origin"]

    AddHeaders --> Handlers["Forward to Route Handlers"]
```

## Dependencies
- `axum::http::{HeaderName, HeaderValue}`
- `std::env`
- `tower_http::cors::{AllowOrigin, CorsLayer}`
- `tower_http::set_header::SetResponseHeaderLayer`
