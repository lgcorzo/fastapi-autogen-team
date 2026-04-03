---
name: FastAPI Connection & Testing
description: Instructions for synchronizing, connecting to, and validating the FastAPI Autogen Team service.
---

# FastAPI Connection & Testing Skill

This skill documents how to interact with the `fastapi-autogen-team` service within the Kubernetes cluster.

## 1. Synchronization (GitOps)

Whenever you make changes to the repository, ensure they are synchronized with the cluster:

```bash
flux reconcile kustomization fastapi-autogen --with-source
```

## 2. API Connectivity

The service is exposed through **LiteLLM** as a gateway.

- **Internal URL**: `http://litellm.llm-apps.svc.cluster.local/v1/chat/completions` (or `10.152.183.237:80`)
- **Model Name**: `internal-gpt4_v0.1`
- **Authentication**: `Bearer sk-1234` (Master Key)

### Sample CURL Command
```bash
curl -X POST "http://10.152.183.237/v1/chat/completions" \
     -H "Content-Type: application/json" \
     -H "Authorization: Bearer sk-1234" \
     -d '{
       "model": "internal-gpt4_v0.1",
       "messages": [{"role": "user", "content": "Explain MLOps"}]
     }'
```

## 3. Testing Scripts

Use the provided Python script for quick validation:
`tests/scripts/test_connection.py`

```bash
python3 tests/scripts/test_connection.py "Your prompt here"
```

## 4. Debugging & Logs

To monitor the agent workflow in real-time (Planner, Searcher, QA steps):

```bash
kubectl logs -f -n llm-apps deployment/fastapi-autogen-team
```

## 5. Artifacts

Execution results are stored in:
`.artifacts/execution_results_[timestamp].json`

Always check this directory for previous test outputs and agent performance logs.
