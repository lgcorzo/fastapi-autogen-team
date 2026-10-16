# AGENTS.md

Instructions and protocols for AI Agents operating on `fastapi-autogen-team`.

## Branch & Pull Request Policy: Human-in-the-Loop (HITL)

- Agents are empowered to create feature branches, commit code, push upstream, create Pull Requests (PRs), and resolve CI/CD failures.
- **STRICT HUMAN-IN-THE-LOOP REQUIREMENT**: Under no circumstances may an agent automatically merge a PR into `main` or default branches.
- The merge process **MUST be a manual human action**.
- Upon ensuring all CI/CD pipelines, linters, and test checks pass with green status, the agent must present the PR link and test evidence to the user and await manual human review and merge.

## Dark Gravity Autonomous Factory Integration

This repository is monitored and autonomously controlled by the **Dark Gravity CA/CD Autonomous Agent Factory** ([`lgcorzo/rust_CACD_autonomous_factory`](https://github.com/lgcorzo/rust_CACD_autonomous_factory)).

### 1. Triggering Missions via Issues

To trigger an autonomous mission, create an issue in this repository:
- **Required Labels** (at least one):
  - `autonomous-mission`
  - `dark-gravity`
- **Resource Limits Definition**:
  Include an explicit resource limit block within the issue description:
  ```markdown
  Resource limits: CPU: 500m, RAM: 512Mi, Timeout: 300s
  ```
- **Autonomous Ingestion**:
  1. The Dark Gravity poller extracts title, description, labels, and resource constraints.
  2. Generates an Ed25519-signed Verifiable Credential for Non-Human Identity (NHI).
  3. Dispatches the mission to the Hatchet orchestrator DAG (`Ingestion` → `Plan` → `Code` → `Validation` → `Review` → `Delivery`).

### 2. Interactive Directives on Pull Requests

Dark Gravity listens to comments on active GitHub Pull Requests. When tagging the bot with a directive:

```text
@darkgravity /<command> [optional prompt/instruction]
```
*(Also accepts `@dark-gravity`)*

#### Supported Directives

| Directive | Description | Agent Action |
|:---|:---|:---|
| `@darkgravity /status` | Queries real-time factory health and DAG state. | Generates a markdown system report with repository, PR target, DAG health, and sandbox status. |
| `@darkgravity /interact <prompt>` | Natural-language query or technical instruction. | Triggers Rustant (Planner) to analyze the query with contextual knowledge and reply directly in the thread. |
| `@darkgravity /refine <instruction>` | Requests localized code edits or targeted bugfixes. | Triggers ZeroClaw (Dev) to apply surgical code mutations in the sandbox. |
| `@darkgravity /validate` | Requests full test and security verification. | Executes automated test suites (cargo check, cargo test, clippy) and SAST security gates within the sandbox. |
