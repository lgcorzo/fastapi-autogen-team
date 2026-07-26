---
type: module
title: "Telemetry Initialization"
description: "OpenTelemetry configuration and tracing setup."
tags: [infrastructure, telemetry, observability, tracing]
last_verified_commit: "722dbbe"
---

# telemetry.rs

This module handles the initialization of OpenTelemetry and connects it to the `tracing` ecosystem, exporting traces to a specified OTLP endpoint.

```mermaid
flowchart TD
    Init["init_telemetry(app_name, endpoint)"]

    Init --> Resource[Create OTel Resource with service.name]
    Resource --> Pipeline[Configure OTLP Pipeline]
    Pipeline --> Exporter[Set HTTP Exporter & Endpoint]
    Exporter --> Tracer[Install Batch Tracer via Tokio]
    Tracer --> TracingLayer[Create tracing_opentelemetry layer]

    TracingLayer --> Registry[Initialize tracing_subscriber Registry]
    Registry --> EnvFilter[Add EnvFilter (default + INFO)]
    Registry --> FmtLayer[Add standard fmt formatting]
    Registry --> GlobalInit[Set Global Default Subscriber]
```
