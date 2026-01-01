# GitOps Deployment Guide

This guide explains how `fastapi-autogen-team` is integrated with the GitOps repository for automated deployments using FluxCD.

## Deployment Overview

The deployment follows a GitOps pattern where the Kubernetes state is synchronized from a dedicated Git repository.

1. **Source Control**: The `gitops_internal_lgcorzo` repository contains a `GitRepository` reference to this project.
2. **Flux Synchronization**: Flux tracks the `main` branch of this repository.
3. **Manifests**: Flux applies the manifests located in `k8s/overlays/gitops/`.
4. **Automatic Updates**: When changes are pushed to `main`, Flux detects them (at a 1-minute interval) and updates the cluster.

### Kubernetes structure

- **Namespace**: `fastapi-autogen`
- **Deployment**: `fastapi-autogen-team` (Port 4100)
- **Overlay**: `k8s/overlays/gitops/kustomization.yaml`

---

## Configuring the GITOPS_TOKEN

The GitHub Action `gitops-trigger.yml` requires a secret named `GITOPS_TOKEN` to interact with the private GitOps repository.


### 1. Generate a Personal Access Token (PAT)

1. Go to your GitHub [Settings](https://github.com/settings/profile).
2. On the left, click **Developer settings** (at the bottom).
3. Click **Personal access tokens** -> **Tokens (classic)**.
4. Click **Generate new token** -> **Generate new token (classic)**.
5. **Note**: Enter something like `GitOps Deploy Token`.
6. **Scopes**: Select **`repo`** (Full control of private repositories).
7. Click **Generate token**.
8. **COPY the token immediately**.

### 2. Add the Secret to this Repository

1. Go to the **Settings** tab of the `fastapi-autogen-team` repository.
2. On the left, click **Secrets and variables** -> **Actions**.
3. Click **New repository secret**.
4. **Name**: `GITOPS_TOKEN`
5. **Secret**: Paste your token.
6. Click **Add secret**.

---

## Manual Deployment Trigger

While Flux automatically synchronizes every minute, you can force a reconciliation if you have `flux` installed and access to the cluster:

```bash
flux reconcile kustomization fastapi-autogen --with-source
```

You can verify the status of the deployment with:

```bash
kubectl get pods -n fastapi-autogen
```
