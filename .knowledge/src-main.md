---
type: script
title: "Main"
source_path: "src/main.rs"
description: "Documentation for src/main.rs."
tags: [script, rust]
last_verified_commit: "cf3c1ee"
---
Source File: `src/main.rs`

## Component Overview

This module defines the `Main` component.

## Architecture

### Class Diagram
```mermaid
classDiagram
    class EmptyComponent
```

### Execution Flow
```mermaid
flowchart TD
    Start --> main
    main --> End
```

## Dependencies
- `dotenvy::dotenv`
- `rust_agent_team::domain::agent::team::AgentTeam`
- `rust_agent_team::infrastructure::telemetry`
- `rust_agent_team::{create_app, AppState}`
- `std::env`
- `std::sync::Arc`
