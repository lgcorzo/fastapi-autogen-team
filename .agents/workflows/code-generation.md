---
description: GUIDELINE for code generation, testing, and DDD compliance
---

# Code Generation Workflow (DDD Standard)

This workflow defines the mandatory steps for all code modifications and feature additions in the `fastapi-autogen-team` repository.

## 1. Research & DDD Planning
Before making any changes, the system **MUST** define an implementation plan that categorizes changes by Domain-Driven Design (DDD) layers:

- **Domain Layer (`src/domain/`)**: Pure business logic, entities, and domain services. No external dependencies.
- **Application Layer (`src/application/`)**: Coordinates tasks and encapsulates domain logic into use cases/DTOs.
- **Infrastructure Layer (`src/infrastructure/`)**: External adapters (R2R, Jira, Database clients, tools).
- **Interface Layer (`src/interface/`)**: HTTP handlers, API routes, and external-facing DTOs.

> [!IMPORTANT]
> The implementation plan must map every new file or modification to its corresponding DDD layer.

## 2. Implementation Execution
- Follow existing patterns for error handling with `AppError` or similar types.
- Ensure all business logic remains in the `domain` or `application` layers.
- Avoid leaking infrastructure details (e.g., specific HTTP error codes) into the domain layer.

## 3. Testing & Validation
Once implementation is complete, the following tests are **REQUIRED**:

- **Unit Tests**: Create unit tests in `tests/unit/` (or matching the module structure) for all new domain/application logic.
- **Integration Tests**: For every new feature or API route, an integration test in `tests/integration/` is mandatory.
- **Security Check**: Verify Header injection and input sanitization for new HTTP handlers.

// turbo-all
## 4. Linting & Formatting
Before committing, run the following commands to ensure code quality:

```bash
# Format code
cargo fmt --all --check

# Run clippy for linting
cargo clippy -- -D warnings
```

> [!CAUTION]
> Do not proceed to commit if linting or formatting checks fail.

## 5. Deployment & Commit
- Commit with a descriptive message (e.g., `feat:`, `fix:`, `refactor:`).
- Push to the `main` branch (or specific feature branch as requested).
- Trigger a Flux reconciliation to synchronize the cluster:
  ```bash
  flux reconcile kustomization fastapi-autogen --with-source
  ```

## 6. Verification & Walkthrough
- Create a `walkthrough.md` summarizing the changes, test results, and deployment status.
- Include logs or audit results to verify the new feature is functional in the cluster environment.
