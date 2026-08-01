# ⚙️ Rust Agent Team Team

Welcome to the documentation for the high-performance Rust service. This project has been fully built using **Axum**, **Rig**, and **Tokio** following **Domain-Driven Design (DDD)** principles to provide a type-safe, concurrent, and highly scalable agentic orchestration platform.

## 🎯 Project Goals
The primary objective of this repository is to orchestrate a team of specialized AI agents to solve complex tasks involving Information Retrieval (RAG) and Issue Tracking (Jira).

### Key Features
- **🚀 DDD Architecture**: Clear separation into Interface, Application, Domain, and Infrastructure layers.
- **🤖 Agentic Orchestration**: Uses the [Rig](https://github.com/0xPlaygrounds/rig) framework for multi-agent workflows.
- **🔍 Advanced Search**: Integrated with R2R for vector-based RAG, Jira for project management, and Confluence for documentation.
- **🛡️ Type Safety**: Full end-to-end type safety with Rust traits and structs.

---

## 🏗️ Architecture Overview
The system follows a tiered DDD structure to decouple the web boundary, the core domain logic, and the external infrastructure tools.

### 🧩 Core Layers
1. **[[v2_architecture#interface-layer|Interface Layer]]**: Handles HTTP requests, streaming responses, and middleware (Security/CORS).
2. **[[v2_architecture#application-layer|Application Layer]]**: Defines DTOs and shared models for data transport.
3. **[[v2_architecture#domain-layer|Domain Layer]]**: The orchestration heart, containing the `AgentTeam` (Planner, Searcher, QA).
4. **[[v2_architecture#infrastructure-layer|Infrastructure Layer]]**: Implements concrete tools (Jira, Confluence, R2R) and telemetry observers.

---

## 🗺️ Documentation Map
- **[[v2_architecture|System Architecture]]**: Detailed design decisions and workflow descriptions.
- **[[data_models|Data Models]]**: Struct definitions for API inputs and agent outputs.
- **[[architecture_modules|Module Structure]]**: Visual map of the Rust DDD package hierarchy including Confluence.
- **[Deployment](https://github.com/lgcorzo/fastapi-autogen-team/blob/main/README.md#usage)**: How to build, test, and deploy the service.

---

## 📊 Interaction Diagrams
- **[[architecture_modules|Package Hierarchy]]**: Visual map of the Rust module structure.
- **[[data_models|Data Relationships]]**: Relationship between the primary API and Agent structs.
- **[[completion_sequence|Sequence Flow]]**: Step-by-step lifecycle of a chat request through DDD layers.

---

## ✅ Current Status
- [x] Rust Migration (v2.0)
- [x] DDD Structural Refactor
- [x] Rig Integration (v0.34.0)
- [x] Axum REST API (v0.7)
- [x] Multi-agent Orchestration
- [x] Integrated Unit & Integration Testing
