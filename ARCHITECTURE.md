# Architecture: `fastapi-autogen-team` in Dark Gravity

## Ecosystem Role & Tier

- **Tier**: `owned_domain`
- **Role**: High-throughput native Rust (`Axum` + `Rig`) microservice exposing OpenAI-compatible streaming SSE multi-agent squad endpoints inside Dark Gravity's `llm-apps` layer.
- **Visibility**: `public`

## Internal Component Design

- `src/` (`Cargo.toml` / `Cargo.lock`): Rust Axum HTTP router and Rig multi-agent squad runtime (`Planner`, `Searcher`, `QA`) with streaming Server-Sent Events (`/agent/api/v1beta/chat/completions`).
- `tests/`, `k8s/`, `Dockerfile`: Automated Rust test suite (`31/31` serialized `--test-threads=1` verification baseline) and hardened container/Kubernetes manifests.
- `openwiki/` & `wiki/`: Generated OKF/architecture documentation verified alongside R2R GraphRAG ingestion (`94` entities, `86` relationships, `2` Leiden communities measured in baseline GraphRAG runs).

## Upstream & Downstream Ecosystem Interfaces

```text
OpenWebUI / External Squad Clients ──► fastapi-autogen-team (Axum SSE :llm-apps)
                                            ├──► Dark-LiteLLM Gateway (LLM routing)
                                            ├──► R2R v3 Engine (GraphRAG retrieval)
                                            └──◄ rust_CACD_autonomous_factory (managed target & CI gate)
```

## Security Boundary & Governance

- **Vertex 4 HITL**: All PRs require passing Cargo checks (`cargo test`, `clippy`) and human review before merging into `main`.
- **`DOC-011` Public Boundary**: Contains zero cluster secrets, private repo names, or internal LAN endpoints.

## Canonical Cross-Links

- [DARK_GRAVITY_MANIFEST.md](./DARK_GRAVITY_MANIFEST.md)
- [REPOSITORIES.md](./REPOSITORIES.md)
- [Global Architecture Portal](https://lgcorzo.github.io/architecture.html)
- [Unified Start-Here Portal](https://lgcorzo.github.io/start-here)
- [AI Auditor Pack](https://lgcorzo.github.io/docs/auditor/)
