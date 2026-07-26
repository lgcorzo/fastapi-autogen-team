---
type: module
title: "HTTP Handlers"
description: "Axum route handlers serving chat completions, model info, and docs."
tags: [interface, http, handlers, axum]
last_verified_commit: "722dbbe"
---

# handlers.rs

This module defines the core HTTP handlers for the Axum web server, connecting incoming REST API requests to the Domain layer orchestration.

```mermaid
flowchart TD
    Req[Incoming HTTP Request]

    Req --> RouteQuery["route_query()"]
    Req --> GetModels["get_models()"]
    Req --> DocsRedirect["docs_redirect()"]

    RouteQuery --> Validate[Validate JSON Input]
    Validate -- Valid --> AgentRun{Is Streaming?}
    Validate -- Invalid --> ErrorResp[400 Bad Request]

    AgentRun -- Stream = true --> AgentTeamRunStream[AgentTeam::run_stream()]
    AgentTeamRunStream --> EmitSSE[Yield SSE Events]
    EmitSSE --> ResponseStream[Streaming Response]

    AgentRun -- Stream = false / None --> AgentTeamRun[AgentTeam::run()]
    AgentTeamRun --> JsonResponse[JSON Completion Output]

    GetModels --> StaticModels[Return hardcoded mock model data]

    DocsRedirect --> Http303[303 See Other Redirect]
```
