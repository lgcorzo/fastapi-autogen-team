# Dark Gravity Ecosystem Repository Map

Dark Gravity is a unified **Continuous Agentic / Continuous Deployment (CA/CD)** Autonomous Software Factory — not a collection of unrelated standalone repositories.

## Canonical Ecosystem Topology

```text
Dark Gravity Autonomous Software Factory
│
├── Core Control Plane & Orchestration
│   ├── rust_CACD_autonomous_factory   # Core 5-crate Rust 2024 orchestrator, AgentWorkspace CRD, Hatchet DAG & runtime MCP
│   ├── speckit-superpowers-bridge     # Spec-Kit (WHAT) <-> Superpowers (HOW) handoff contract & boundary guard
│   ├── Internal GitOps Control Plane  # Pull-based FluxCD v2 cluster reconciler, SealedSecrets, OpenZiti & NetworkPolicies
│   └── Internal Incident Remediation  # FluxCD alert classifier, MLflow tracker & autonomous patch synthesizer
│
├── Public Knowledge Hub & Agent Entry
│   ├── lgcorzo.github.io              # /start-here, /ai-agents, RESEARCH.md, EXPERIMENTS.md, /docs/auditor/, KG, Metrics & Rust dark-gravity-mcp
│   └── lgcorzo                        # GitHub Profile entry point routing reviewers & agents to the ecosystem
│
├── Owned Applications & Domain Standards
│   ├── mlops-python-package           # Enterprise MLOps standard (DVC, MLflow, Hydra, SHAP, CycloneDX, OpenWiki)
│   ├── llmops-python-package          # ISO 42010/15289 LLMOps platform (Hatchet DSL, MCP registry, OpenWiki)
│   └── fastapi-autogen-team           # High-throughput Rust (Axum + Rig) streaming SSE multi-agent squad service
│
└── Maintained Sovereign Infrastructure Forks (42 forks under MAINTAINED_FORK_PROFILE)
    ├── R2R-Engine / R2R-Application   # Hybrid pgvector + Leiden GraphRAG corporate memory
    ├── dark-litellm                   # Sovereign LLM router & FinOps X-Vtag priority policy gateway
    ├── deepwiki-rs                    # Tree-sitter Rust AST analyzer & Orphan Symbol Rate (OSR < 5%) verifier
    ├── semantica                      # Causal provenance graph & conflict detection engine
    ├── spec-kit / superpowers         # Spec-Driven Development & execution discipline upstreams
    └── MinIO S3 & SIMD Stack          # 38 Go/S3/KMS/SIMD sovereign forks (lgcorzo/kes archived FROZEN_READONLY)
```

## Canonical Repository Matrix

| Repository | Tier | Primary Language | Factory Role | Visibility | Fork Profile / Policy | Key Dependencies |
|---|---|---|---|---|---|---|
| `rust_CACD_autonomous_factory` | `core_factory` | Rust | Core CA/CD orchestrator, CRD operator, Hatchet DAG & runtime MCP | `public` | Original | `speckit-superpowers-bridge`, Hatchet, Kafka, R2R, gVisor |
| `Internal GitOps Control Plane` | `private_gitops` | YAML | FluxCD v2 reconciler, SealedSecrets, OpenZiti & NetworkPolicies | `private` | Original (`DOC-011` alias) | `rust_CACD_autonomous_factory`, Vault, Keycloak, MinIO |
| `Internal Incident Remediation Service` | `private_gitops` | Python | FluxCD alert classifier & automated patch synthesis daemon | `private` | Original (`DOC-011` alias) | Internal GitOps Control Plane, MLflow, Dark-LiteLLM |
| `speckit-superpowers-bridge` | `orchestration_bridge` | Shell/Markdown | Spec-Kit (`WHAT`) <-> Superpowers (`HOW`) handoff & guard contract | `public` | Original | `spec-kit`, `superpowers`, `rust_CACD_autonomous_factory` |
| `lgcorzo.github.io` | `public_portal` | HTML/Python/Rust | Portal, `/docs/auditor/`, KG, Metrics & `dark-gravity-mcp` crate | `public` | Original | `rust_CACD_autonomous_factory`, `R2R-Engine` |
| `lgcorzo` | `public_portal` | Markdown | GitHub Profile ecosystem entry & topology overview | `public` | Original | `lgcorzo.github.io`, `rust_CACD_autonomous_factory` |
| `mlops-python-package` | `owned_domain` | Python | Enterprise MLOps reference & mission target (`#476`, `#478`) | `public` | Original | `rust_CACD_autonomous_factory`, MLflow, R2R |
| `llmops-python-package` | `owned_domain` | Python | ISO 42010/15289 LLMOps platform, MCP & OpenWiki | `public` | Original | `rust_CACD_autonomous_factory`, Dark-LiteLLM, R2R |
| `fastapi-autogen-team` | `owned_domain` | Rust | Native Axum + Rig streaming SSE multi-agent microservice | `public` | Original | `rust_CACD_autonomous_factory`, R2R, Dark-LiteLLM |
| `dark-litellm` | `maintained_fork` | Python | Hardened LLM proxy with FinOps `X-Vtag-*` & priority scheduler | `public` | `MAINTAINED_FORK_PROFILE` | Dark-LiteLLM service |
| `deepwiki-rs` | `maintained_fork` | Rust | Tree-sitter AST analyzer & `OSR < 5%` verification | `public` | `MAINTAINED_FORK_PROFILE` | R2R GraphRAG |
| `semantica` | `maintained_fork` | Python | Causal provenance ontology & lane conflict detector | `public` | `MAINTAINED_FORK_PROFILE` | Kafka `agent-thought`, MinIO |
| `R2R-Engine` / `R2R-Application` | `maintained_fork` | Python/TS | Hybrid `pgvector` + Leiden GraphRAG corporate memory | `public` | `MAINTAINED_FORK_PROFILE` | Hatchet, CloudNativePG |
| `minio` / `operator` / SIMD stack | `maintained_fork` | Go | Sovereign S3 storage, KMS & AVX-512/NEON hashing (`kes` archived) | `public` | `MAINTAINED_FORK_PROFILE` (`kes`: `FROZEN_READONLY`) | Sovereign Storage Namespace |

## Portfolio Statistics & Fork Policy (`data/canonical-claims.json`)

- **Canonical Public Portfolio**: `64` public GitHub repositories = `22` original + `42` maintained forks (`5` fork categories: `4` agent/spec tooling, `5` memory/docs/gateway, `10` storage platform, `17` Go libraries, `6` experiments/learning).
- **Portfolio Baselines**: `69` historical baseline (with `5` private/archived repos); `72` Spec `004` inventory (`66` public + `6` private).
- **Fork Governance**: Active maintained forks follow `MAINTAINED_FORK_PROFILE` (preserve upstream paths and `LICENSE`, no `upstream` remote, Fork Notice preamble, Private Security Advisories, `[agent]` commit prefix); `lgcorzo/kes` stays permanently `FROZEN_READONLY`.
