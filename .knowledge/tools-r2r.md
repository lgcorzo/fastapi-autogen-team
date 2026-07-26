---
type: class
title: "R2RTool"
description: "Tool for executing RAG (Retrieval-Augmented Generation) vector searches in R2R."
tags: [infrastructure, tools, r2r, rag]
last_verified_commit: "722dbbe"
---

# r2r.rs

This module provides the `R2RTool`, responsible for authenticating and querying the external R2R vector database for contextual information retrieval.

```mermaid
classDiagram
    class R2RArgs {
        +String query
    }

    class R2RError {
        <<enumeration>>
        EnvVarMissing(VarError)
        RequestError(reqwest::Error)
        Other(String)
    }

    class R2RTool {
        +NAME: &'static str$
        +definition(String prompt) ToolDefinition
        +call(R2RArgs args) Result~String, R2RError~
    }
```
