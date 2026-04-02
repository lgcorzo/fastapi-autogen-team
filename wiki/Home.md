# ⚙️ FastAPI Autogen Team (Rust Refresh)

Welcome to the documentation for the high-performance Rust service migration of the `fastapi-autogen-team`. This project has been fully rebuilt using **Axum**, **Rig**, and **Tokio** to provide a type-safe, concurrent, and highly scalable agentic orchestration platform.

## 🎯 Project Goals
The primary objective of this repository is to orchestrate a team of specialized AI agents to solve complex tasks involving Information Retrieval (RAG) and Issue Tracking (Jira).

### Key Features
- **🚀 High Performance**: Built with Rust for maximum throughput and minimal memory footprint.
- **🤖 Agentic Orchestration**: Uses the [Rig](https://github.com/0xPlaygrounds/rig) framework for multi-agent workflows.
- **🔍 Advanced Search**: Integrated with R2R for vector-based RAG and Jira for project management.
- **🛡️ Type Safety**: Full end-to-end type safety with Rust traits and structs.

---

## 🏗️ Architecture Overview
The system is composed of an **Axum** web server that exposes a REST API, and a core **AgentTeam** that handles orchestration.

### 🧩 Core Components
1. **[Axum API](v2_architecture.md#axum-api)**: Handles HTTP requests, streaming responses, and state management.
2. **[Rig Agent Team](v2_architecture.md#agent-orchestration)**: A specialized triad consisting of:
    - **Planner**: Deconstructs requests into actionable steps.
    - **Searcher**: Executes tools (Jira/R2R) to gather context.
    - **QA Agent**: Refines and validates the final response.
3. **[Tools](v2_architecture.md#tool-integrations)**: Concrete implementations of search and tracking capabilities.

---

## 🗺️ Documentation Map
- **[System Architecture](v2_architecture.md)**: Detailed design decisions and workflow descriptions.
- **[Data Models](data_models.md)**: Struct definitions for API inputs and agent outputs.
- **[CI/CD & Deployment](../README.md#🚀-quick-start)**: How to build, test, and deploy the service.

---

## 📊 Interaction Diagrams
- **[Package Hierarchy](architecture_modules.md)**: Visual map of the Rust module structure.
- **[Data Relationships](data_models.md)**: Relationship between the primary API and Agent structs.
- **[Sequence Flow](completion_sequence.md)**: Step-by-step lifecycle of a chat request.

---

## ✅ Current Status
- [x] Rust Migration (v2.0)
- [x] Rig Integration (v0.34.0)
- [x] Axum REST API (v0.7)
- [x] Multi-agent Orchestration
- [x] Integrated Unit & Integration Testing
