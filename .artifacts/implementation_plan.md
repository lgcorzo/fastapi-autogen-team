# Resolve Pod Log Errors in fastapi-autogen-team

The user requested to check and solve the logs in pod `fastapi-autogen-team-6cb5c65c99-ghdw6`.
Research reveals two main issues:
1. **401 Unauthorized**: Authentication failure when calling LiteLLM due to a mismatch between the pod's `LITELLM_API_KEY` and LiteLLM's `LITELLM_MASTER_KEY`.
2. **404 Not Found (OpenTelemetry)**: The OTLP exporter is hitting a malformed URL (`.../v1/traces/v1/traces`) due to double-appending signals in the configuration and code.

## Proposed Changes

### [fastapi-autogen-team]

#### [MODIFY] [team.rs](file:///mnt/F024B17C24B145FE/Repos/fastapi-autogen-team/src/domain/agent/team.rs)
- Strengthen the `Planner` agent's preamble to strictly forbid JSON and Markdown formatting.
- Add basic filtering to `queries.lines()` to skip lines starting with JSON punctuation (`{`, `}`, `[`).
- Update the `QA` agent to consistently terminate and handle empty search results gracefully.
- Consolidate the `run` and `run_stream` logic to share a more robust search-then-synthesize flow.

#### [DONE] [deployment.yaml](file:///mnt/F024B17C24B145FE/Repos/fastapi-autogen-team/k8s/base/deployment.yaml)
- Resolved pull policy and env mapping issues.

#### [DONE] [telemetry.rs](file:///mnt/F024B17C24B145FE/Repos/fastapi-autogen-team/src/infrastructure/telemetry.rs)
- Resolved OTel 404 errors.

### [gitops_internal_lgcorzo]

#### [MODIFY] [fastapi-autogen-secrets] (Kubernetes Secret)
- Since this is managed via GitOps, I need to update the `SealedSecret` in the `fastapi-autogen-team` repo.
- However, since I cannot easily "seal" a new secret without the controller's public key, I will update the `.env` file first.
- I will also attempt to patch the live secret in the cluster for immediate verification.

---

## Verification Plan

### Automated Tests
- No specific automated tests required for these infrastructure/config fixes, but I will monitor the pod logs.

### Manual Verification
1. Apply the environment variable changes to the pod (by updating the secret and restarting).
2. Check `kubectl logs fastapi-autogen-team-6cb5c65c99-ghdw6 -n llm-apps --follow`.
3. Verify that `401 Unauthorized` errors disappear.
4. Verify that `OpenTelemetry trace error` (404) disappears.
