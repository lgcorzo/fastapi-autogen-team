---
type: module
title: "Telemetry"
source_path: "src/infrastructure/telemetry.rs"
description: "Documentation for src/infrastructure/telemetry.rs."
tags: [module, rust]
last_verified_commit: "cf3c1ee"
---
Source File: `src/infrastructure/telemetry.rs`

## Component Overview

This module defines the `Telemetry` component.

## Architecture

### Class Diagram
```mermaid
classDiagram
    class EmptyComponent
```

### Execution Flow
```mermaid
flowchart TD
    Init["init_telemetry(app_name, endpoint)"]

    Init --> Resource["Create OTel Resource with service.name"]
    Resource --> Pipeline["Configure OTLP Pipeline"]
    Pipeline --> Exporter["Set HTTP Exporter & Endpoint"]
    Exporter --> Tracer["Install Batch Tracer via Tokio"]
    Tracer --> TracingLayer["Create tracing_opentelemetry layer"]

    TracingLayer --> Registry["Initialize tracing_subscriber Registry"]
    Registry --> EnvFilter["Add EnvFilter (default + INFO)"]
    Registry --> FmtLayer["Add standard fmt formatting"]
    Registry --> GlobalInit["Set Global Default Subscriber"]
```

## Dependencies
- `opentelemetry::KeyValue`
- `opentelemetry_otlp::WithExportConfig`
- `opentelemetry_sdk::{runtime, trace::Config, Resource}`
- `tracing_subscriber::{layer::SubscriberExt, util::SubscriberInitExt, EnvFilter}`
