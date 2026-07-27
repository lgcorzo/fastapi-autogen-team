---
type: module
title: "Tools Module"
source_path: "src/infrastructure/tools/mod.rs"
description: "Documentation for src/infrastructure/tools/mod.rs."
tags: [module, rust]
last_verified_commit: "1997254"
---
Source File: `src/infrastructure/tools/mod.rs`

## Component Overview

This module exports the available search tools for the application.

## Architecture

### Class Diagram
```mermaid
classDiagram
    class ToolsModule {
        <<module>>
    }
```

### Dependency Edges
```mermaid
flowchart TD
    ToolsModule --> ConfluenceTool
    ToolsModule --> JiraTool
    ToolsModule --> R2RTool
    ToolsModule --> SearchTool
```

## Dependencies
- `confluence`
- `jira`
- `r2r`
- `search`